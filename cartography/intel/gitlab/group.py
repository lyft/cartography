import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from requests.exceptions import RequestException

from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def get_groups(access_token: str):
    """
    As per the rest api docs:https://docs.gitlab.com/ee/api/api_resources.html
    """
    url = f"https://gitlab.example.com/api/v4/groups?pagelen=100"

    response = make_requests_url(url,access_token)
    groups = response.json()

    while 'next' in response:
        response = make_requests_url(response.get('next'),access_token)
        groups.extend(response.json())

    return groups

def load_group_data(session: neo4j.Session, group_data: List[Dict], common_job_parameters: Dict) -> None:
    session.write_transaction(_load_group_data, group_data, common_job_parameters)

def _load_group_data(tx: neo4j.Transaction, group_data: List[Dict], common_job_parameters: Dict):
    ingest_group = """
    MERGE (group:GitLabGroup{id: $id})
    ON CREATE SET
        group.firstseen = timestamp(),
        group.created_at = $created_at

    SET
        group.path = $path,
        group.name = $name,
        group.description = $description,
        group.visibility = $visibility,
        group.web_url = $web_url,
        group.avatar_url = $avatar_url,
        group.updated_at = $updated_at

    WITH group

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (group)<-[o:OWNER]-(owner)
    ON CREATE SET
        o.firstseen = timestamp()
    SET
        o.lastupdated = $UpdateTag

    """
    for group in group_data:
        tx.run(
            ingest_group,
            name=group.get("name"),
            created_on=group.get('created_at'),
            path=group.get('path'),
            description=group.get('description'),
            visibility=group.get('visibility'),
            web_url=group.get('web_url'),
            avatar_url=group.get('avatar_url'),
            UpdateTag=common_job_parameters['UPDATE_TAG'],
            workspace_id=common_job_parameters['WORKSPACE_ID'],
        )

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gitlab_group_cleanup.json', neo4j_session, common_job_parameters)

def sync(
        neo4j_session: neo4j.Session,
        groups: List[Dict],
        common_job_parameters: Dict[str, Any],

) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Gitlab All groups")

    load_group_data(neo4j_session, groups, common_job_parameters)

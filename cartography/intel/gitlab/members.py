import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from requests.exceptions import RequestException

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def get_group_members(access_token:str,group:str):
    """
    As per the rest api docs:https://docs.gitlab.com/ee/api/members.html
    Pagination: https://docs.gitlab.com/ee/api/rest/index.html#pagination
    """
    url = f"https://gitlab.com/api/v4/groups/{group}/members?per_page=100"
    members = paginate_request(url, access_token)

    return members



def load_members_data(session: neo4j.Session, members_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_members_data, members_data,  common_job_parameters)


def _load_members_data(tx: neo4j.Transaction,members_data:List[Dict],common_job_parameters:Dict):
    ingest_group="""
    UNWIND $membersData as member
    MERGE (mem:GitLabMember {id: member.id})
    ON CREATE SET mem.firstseen = timestamp(),
    mem.created_at = member.created_at

    SET mem.name = member.name,
    mem.id = member.id,
    mem.username = member.username,
    mem.state = member.state,
    mem.profile_url = member.web_url,
    mem.created_by = member.created_by.username,
    mem.lastupdated = $UpdateTag

    WITH mem,member
    MATCH (owner:GitLabGroup {id: member.group_id})
    merge (owner)-[o:MEMBER]->(mem)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    tx.run(
        ingest_group,
        membersData=members_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gitlab_group_member_cleanup.json', neo4j_session, common_job_parameters)


def sync(
        neo4j_session: neo4j.Session,
        group_id:str,
        group_name:str,
        access_token:str,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Gitlab All group members")
    group_members=get_group_members(access_token,group_id)
    load_members_data(neo4j_session,group_members,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)

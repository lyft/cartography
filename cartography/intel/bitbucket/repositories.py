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
def get_repos(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    return make_requests_url(url,access_token)

def load_repositeris_data(session: neo4j.Session, repos_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_repositeris_data, repos_data,  common_job_parameters)

def _load_repositeris_data(tx: neo4j.Transaction,repos_data:List[Dict],common_job_parameters:Dict):
    ingest_repositeris="""
    UNWIND $reposData as repo
    MERGE (re:BitbucketRepository{id:repo.uuid})
    ON CREATE SET re.firstseen = timestamp(),
    re.created_on = repo.created_on

    SET re.slug = repo.slug,
    re.type = repo.type,
    re.uuid = repo.uuid,
    re.name=repo.name,
    re.is_private = repo.is_private,
    re.description=repo.description,
    re.full_name=repo.full_name,
    re.has_issues=repo.has_issues,
    re.language=repo.language,
    re.owner=repo.owner.display_name,
    re.parent=repo.parent.name,
    re.lastupdated = $UpdateTag
    WITH re,repo
    MATCH (project:BitbucketProjects{id:repo.project.uuid})
    merge (project)<-[o:REPOSITORY]-(re)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """

    tx.run(
        ingest_repositeris,
        reposData=repos_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('bitbucket_workspace_repositories_cleanup.json', neo4j_session, common_job_parameters)

def sync(
        neo4j_session: neo4j.Session,
        workspace_name:str,
        bitbucket_refresh_token:str,
        common_job_parameters: Dict[str, Any],

) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Bitbucket All Repositories")
    workspace_repos=get_repos(bitbucket_refresh_token,workspace_name)
    load_repositeris_data(neo4j_session,workspace_repos,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)

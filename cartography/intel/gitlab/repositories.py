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
def get_repos(access_token:str,project:str):
    """
    As per the rest api docs:https://docs.gitlab.com/ee/api/repositories.html
    """
    
    url = f"https://gitlab.example.com/api/v4/projects/{project}/repository/tree?per_page=100"

    response = make_requests_url(url,access_token)
    repositories = response.json()

    while 'next' in response:
        response = make_requests_url(response.get('next'),access_token)
        repositories.extend(response.json())

    return repositories

def load_repositories_data(session: neo4j.Session, repos_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_repositories_data, repos_data,  common_job_parameters)


def _load_repositories_data(tx: neo4j.Transaction,repos_data:List[Dict],common_job_parameters:Dict):
    ingest_repositories="""
    UNWIND $reposData as repo
    MERGE (re:GitLabRepository{id: repo.id})
    ON CREATE SET re.firstseen = timestamp(),
    re.created_at = repo.created_at

    SET re.name = repo.name,
    re.description = repo.description,
    re.visibility = repo.visibility,
    re.path_with_namespace = repo.path_with_namespace,
    re.default_branch = repo.default_branch,
    re.ssh_url_to_repo = repo.ssh_url_to_repo,
    re.http_url_to_repo = repo.http_url_to_repo,
    re.web_url = repo.web_url,
    re.last_activity_at = repo.last_activity_at,
    re.owner_username = repo.owner.username,
    re.owner_id = repo.owner.id,
    re.namespace_id = repo.namespace.id,
    re.namespace_name = repo.namespace.name,
    re.lastupdated = $UpdateTag
    
    WITH re, repo
    MATCH (project:GitLabProject{id: repo.namespace.id})
    MERGE (project)<-[o:HAS]-(re)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_repositories,
        reposData=repos_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gitlab_project_repositories_cleanup.json', neo4j_session, common_job_parameters)


def sync(
        neo4j_session: neo4j.Session,
        project_id:str,
        gitlab_access_token:str,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Gitlab All Repositories")
    project_repos=get_repos(gitlab_access_token,project_id)
    load_repositories_data(neo4j_session,project_repos,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)

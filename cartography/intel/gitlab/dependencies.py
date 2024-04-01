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
def get_dependencies(access_token:str,project:str):
    """
    As per the rest api docs:https://docs.gitlab.com/ee/api/dependencies.html
    """
    
    url = f"https://gitlab.example.com/api/v4/projects/{project}/dependencies?per_page=100"

    response = make_requests_url(url,access_token)
    dependencies = response.json()

    while 'next' in response:
        response = make_requests_url(response.get('next'),access_token)
        dependencies.extend(response.json())

    return dependencies

def load_dependencies_data(session: neo4j.Session, dependencies_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_dependencies_data, dependencies_data,  common_job_parameters)


def _load_dependencies_data(tx: neo4j.Transaction,dependencies_data:List[Dict],common_job_parameters:Dict):
    ingest_dependencies="""
    UNWIND $dependenciesData AS dependency
    MERGE (dep:GitLabDependency {id: dependency.id})
    ON CREATE SET dep.firstseen = timestamp()
    dep.created_on = dependency.created_on

    SET dep.name = dependency.name,
    dep.version = dependency.version,
    dep.type = dependency.type,
    dep.description = dependency.description,
    dep.lastupdated = $UpdateTag

    WITH dep, dependency
    MATCH (repo:GitLabRepository {id: dependency.repository_id})
    MERGE (dep)-[r:HAS]->(repo)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_dependencies,
        dependenciesData=dependencies_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gitlab_project_dependencies_cleanup.json', neo4j_session, common_job_parameters)


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
    logger.info("Syncing Gitlab All Dependencies")
    project_dependencies=get_dependencies(gitlab_access_token,project_id)
    load_dependencies_data(neo4j_session,project_dependencies,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)

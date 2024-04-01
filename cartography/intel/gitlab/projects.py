import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)


@timeit
def get_projects(access_token:str,group:str):
    """
    As per the rest api docs:https://docs.gitlab.com/ee/api/api_resources.html#project-resources
    """
    
    url = f"https://gitlab.example.com/api/v4/projects?per_page=100"

    response = make_requests_url(url,access_token)
    projects = response.json()

    while 'next' in response:
        response = make_requests_url(response.get('next'),access_token)
        projects.extend(response.json())

    return projects


def load_projects_data(session: neo4j.Session, project_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_projects_data, project_data,  common_job_parameters)


def _load_projects_data(tx: neo4j.Transaction,project_data:List[Dict],common_job_parameters:Dict):
    ingest_group="""
    UNWIND $projectData as project
    MERGE (pro:GitLabProject {id: project.id})
    ON CREATE SET pro.firstseen = timestamp(),
    pro.created_on = project.created_at

    SET pro.description = project.description,
    pro.name = project.name,
    pro.visibility = project.visibility,
    pro.path_with_namespace = project.path_with_namespace,
    pro.http_url_to_repo = project.http_url_to_repo,
    pro.ssh_url_to_repo = project.ssh_url_to_repo,
    pro.web_url = project.web_url,
    pro.last_activity_at = project.last_activity_at,
    pro.lastupdated = $UpdateTag

    WITH pro,project
    MATCH (group:GitLabGroup {id: member.group_id})
    merge (group)-[o:RESOURCE]->(pro)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_group,
        projectData=project_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session,  common_job_parameters: Dict) -> None:
    run_cleanup_job('gitlab_group_project_cleanup.json', neo4j_session, common_job_parameters)


def sync(
        neo4j_session: neo4j.Session,
        group_name:str,
        gitlab_access_token:str,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Gitlab All group Projects ")
    group_projects=get_projects(gitlab_access_token,group_name)
    load_projects_data(neo4j_session,group_projects,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)

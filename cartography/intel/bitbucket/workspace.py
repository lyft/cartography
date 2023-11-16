import requests
import json
import configparser
import logging
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from requests.exceptions import RequestException
# from bitbucket.client import Client
# from bitbucket.exceptions import BaseError
import neo4j
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from cartography.intel.github.util import fetch_all
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)

@timeit
def get_workspaces(access_token:str):
    url = f"https://api.bitbucket.org/2.0/workspaces"
    return make_requests_url(url,access_token)

@timeit
def get_workspace_members(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members"
    return make_requests_url(url,access_token)

@timeit
def get_repos(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    return make_requests_url(url,access_token)

@timeit
def get_projects(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/projects"
    return make_requests_url(url,access_token)

def make_requests_url(url,access_token):
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
            }
        response = requests.request(
            "GET",
            url,
            headers=headers
            )
        if response.status_code!=200:
            return []
        return response.json().get('values',[])
    except RequestException as e:
        logger.info(f"failed to geting bitbucket response")
        return []
    

def load_workspace_data(neo4j_session: neo4j.Session,workspace_data:List[Dict],common_job_parameters:Dict):
    ingest_workspace="""
        UNWIND $workspaceData as workspace
    MERGE (work:BitbucketWorkspace{name: workspace.name})
    ON CREATE SET 
        work.firstseen = timestamp(),
        work.created_on = workspace.created_on

    SET 
        work.slug = workspace.slug,
        work.type = workspace.type,
        work.uuid = workspace.uuid,
        work.is_private = workspace.is_private,
        work.lastupdated = $UpdateTag

    WITH work

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (work)<-[o:OWNER]-(owner)
    ON CREATE SET 
        o.firstseen = timestamp()
    SET 
        o.lastupdated = $UpdateTag

    """
    neo4j_session.run(
        ingest_workspace,
        workspaceData=workspace_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
        workspace_id=common_job_parameters['WORKSPACE_ID'],
    )
    
    
    
def load_projects_data(neo4j_session: neo4j.Session,project_data:List[Dict],common_job_parameters:Dict):
    ingest_workspace="""
    UNWIND $projectData as project
    MERGE (pro:BitbucketProjects{name: project.name})
    ON CREATE SET pro.firstseen = timestamp(),
    pro.created_on = project.created_on

    SET pro.description = project.description,
    pro.type = project.type,
    pro.uuid = project.uuid,
    pro.is_private = project.is_private,
    pro.has_publicly_visible_repos=project.has_publicly_visible_repos,
    pro.key=project.key,
    pro.owner=project.owner.display_name,
    pro.type=project.type,
    pro.updated_on=project.updated_on,
    pro.lastupdated = $UpdateTag

    WITH pro,project
    MATCH (work:BitbucketWorkspace{name:project.workspace.name})
    merge (work)-[o:PROJETS]->(pro)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    neo4j_session.run(
        ingest_workspace,
        projectData=project_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )
    
def load_repositeris_data(neo4j_session: neo4j.Session,repos_data:List[Dict],common_job_parameters:Dict):
    ingest_repositeris="""
    UNWIND $reposData as repo
    MERGE (re:BitbucketRepository{name:repo.name})
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
    MATCH (project:BitbucketProjects{name:repo.project.name})
    merge (project)<-[o:REPOSITORY]-(re)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
   
    neo4j_session.run(
        ingest_repositeris,
        reposData=repos_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )
    
def load_memebers_data(neo4j_session: neo4j.Session,members_data:List[Dict],common_job_parameters:Dict):
    ingest_workspace="""
    UNWIND $membersData as member
    MERGE (mem:BitbucketMember{name: member.user.display_name})
    ON CREATE SET mem.firstseen = timestamp()

    SET mem.slug = member.slug,
    mem.type = member.user.type,
    mem.account_id=member.user.account_id,
    mem.uuid = member.user.uuid,
    mem.lastupdated = $UpdateTag

    WITH mem,member
    MATCH (owner:BitbucketWorkspace{name:member.workspace.name})
    merge (owner)-[o:MEMBER]->(mem)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    neo4j_session.run(
        ingest_workspace,
        membersData=members_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )
          
    
def sync(
        neo4j_session: neo4j.Session,
        common_job_parameters: Dict[str, Any],
        bitbucket_refresh_token: str,
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param bitbucket_refresh_token: The API key to access the GitHub v4 API
    :return: Nothing
    """
    logger.info("Syncing Bitbucket All workspaces")
    workspace_data = get_workspaces(bitbucket_refresh_token)
    
    members=[]
    repos=[]
    projects=[]
    for workspace in workspace_data:
        workspace_members=get_workspace_members(bitbucket_refresh_token,workspace.get('name'))
        members.extend(workspace_members)
        workspace_repos=get_repos(bitbucket_refresh_token,workspace.get('name'))
        repos.extend(workspace_repos)
        workspace_projects=get_projects(bitbucket_refresh_token,workspace.get('name'))
        projects.extend(workspace_projects)
        
    load_workspace_data(neo4j_session,workspace_data,common_job_parameters)
    load_projects_data(neo4j_session,projects,common_job_parameters)
    load_repositeris_data(neo4j_session,repos,common_job_parameters)
    load_memebers_data(neo4j_session,members,common_job_parameters)
    run_cleanup_job('bitbucket_workspace_cleanup.json', neo4j_session, common_job_parameters)

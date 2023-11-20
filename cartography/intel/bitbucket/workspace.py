import requests
import logging
from typing import Any
from typing import Dict
from typing import List
from requests.exceptions import RequestException
import neo4j
from cartography.util import run_cleanup_job
from cartography.util import make_requests_url
from cartography.util import timeit
logger = logging.getLogger(__name__)

@timeit
def get_workspaces(access_token:str):
    url = f"https://api.bitbucket.org/2.0/workspaces"
    return make_requests_url(url,access_token)

def load_workspace_data(neo4j_session: neo4j.Session,workspace_data:List[Dict],common_job_parameters:Dict):
    ingest_workspace="""
    MERGE (work:BitbucketWorkspace{name: $name})
    ON CREATE SET 
        work.firstseen = timestamp(),
        work.created_on = $created_on

    SET 
        work.slug = $slug,
        work.type = $type,
        work.uuid = $uuid,
        work.is_private = $is_private,
        work.lastupdated = $UpdateTag

    WITH work

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (work)<-[o:OWNER]-(owner)
    ON CREATE SET 
        o.firstseen = timestamp()
    SET 
        o.lastupdated = $UpdateTag

    """
    for workspace in workspace_data: 
        neo4j_session.run(
            ingest_workspace,
            name=workspace.get("name"),
            created_on=workspace.get('created_on'),
            slug=workspace.get('slug'),
            type=workspace.get('type'),
            uuid=workspace.get('uuid'),
            is_private=workspace.get('is_private'),
            UpdateTag=common_job_parameters['UPDATE_TAG'],
            workspace_id=common_job_parameters['WORKSPACE_ID'],
        )
        cleanup(neo4j_session,workspace.get('uuid'),common_job_parameters)
    
def cleanup(neo4j_session: neo4j.Session, workspace_uuid: str, common_job_parameters: Dict) -> None:
    common_job_parameters['WORKSPACE_UUID']=workspace_uuid
    run_cleanup_job('bitbucket_workspace_cleanup.json', neo4j_session, common_job_parameters)
   
    
def sync(
        neo4j_session: neo4j.Session,
        workspaces:List[Dict],
        common_job_parameters: Dict[str, Any],
        
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Bitbucket All workspaces")
    load_workspace_data(neo4j_session,workspaces,common_job_parameters)
    
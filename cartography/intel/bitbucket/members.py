import requests
import logging
from typing import Any
from typing import Dict
from typing import List
from requests.exceptions import RequestException
import neo4j
from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)

@timeit
def get_workspace_members(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members"
    return make_requests_url(url,access_token)



    
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
    
    cleanup(neo4j_session,common_job_parameters)
    
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('bitbucket_workspace_member_cleanup.json', neo4j_session, common_job_parameters)
         
    
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
    logger.info("Syncing Bitbucket All workspace members")
    workspace_members=get_workspace_members(bitbucket_refresh_token,workspace_name)
    load_memebers_data(neo4j_session,workspace_members,common_job_parameters)
    

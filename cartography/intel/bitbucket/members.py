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
def get_workspace_members(access_token:str,workspace:str):
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members"
    return make_requests_url(url,access_token)


def transform_members(workspace_members: List[Dict]) -> List[Dict]:
    for member in workspace_members:
        member['workspace']['uuid'] = member['workspace']['uuid'].replace('{','').replace('}','')
        member['user']['uuid'] = member['user']['uuid'].replace('{','').replace('}','')

    return workspace_members


def load_members_data(session: neo4j.Session, members_data:List[Dict],common_job_parameters:Dict) -> None:
    session.write_transaction(_load_members_data, members_data,  common_job_parameters)


def _load_members_data(tx: neo4j.Transaction,members_data:List[Dict],common_job_parameters:Dict):
    ingest_workspace="""
    UNWIND $membersData as member
    MERGE (mem:BitbucketMember{id: member.user.uuid})
    ON CREATE SET mem.firstseen = timestamp()

    SET mem.slug = member.slug,
    mem.type = member.user.type,
    mem.name= member.user.display_name,
    mem.account_id=member.user.account_id,
    mem.uuid = member.user.uuid,
    mem.lastupdated = $UpdateTag

    WITH mem,member
    MATCH (owner:BitbucketWorkspace{id:member.workspace.uuid})
    merge (owner)-[o:MEMBER]->(mem)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    tx.run(
        ingest_workspace,
        membersData=members_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('bitbucket_workspace_member_cleanup.json', neo4j_session, common_job_parameters)


def sync(
        neo4j_session: neo4j.Session,
        workspace_name:str,
        bitbucket_access_token:str,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    logger.info("Syncing Bitbucket All workspace members")
    workspace_members=get_workspace_members(bitbucket_access_token,workspace_name)
    workspace_members=transform_members(workspace_members)
    load_members_data(neo4j_session,workspace_members,common_job_parameters)
    cleanup(neo4j_session,common_job_parameters)
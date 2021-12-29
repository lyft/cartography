import logging
from typing import Dict

import neo4j

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_tenant_id(credentials: Credentials) -> str:
    return credentials.get_tenant_id()


def load_azure_tenant(
    neo4j_session: neo4j.Session, tenant_id: str, current_user: Dict, update_tag: int, common_job_parameters: Dict,
) -> None:
    query = """
    MERGE (w:CloudanixWorkspace{id: {workspaceID}})
    SET w.lastupdated = {update_tag}
    WITH w
    MERGE (at:AzureTenant{id: {tenantID}})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = {update_tag}
    WITH w, at
    MERGE (w)-[o:OWNER]->(at)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = {update_tag}
    WITH at
    MERGE (ap:AzurePrincipal{id: {userEmail}})
    ON CREATE SET ap.email = {userEmail}, ap.firstseen = timestamp()
    SET ap.lastupdated = {update_tag},
    ap.name={userName}, ap.userid={userID}
    WITH at, ap
    MERGE (at)-[r:RESOURCE]->(ap)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag};
    """
    neo4j_session.run(
        query,
        workspaceID=common_job_parameters['WORKSPACE_ID'],
        tenantID=tenant_id,
        userEmail=current_user['email'],
        userID=current_user.get('id'),
        userName=current_user.get('name'),
        update_tag=update_tag,

    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_tenant_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, tenant_id: str, current_user: Dict, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    common_job_parameters['AZURE_TENANT_ID'] = tenant_id

    load_azure_tenant(neo4j_session, tenant_id, current_user, update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

    del common_job_parameters['AZURE_TENANT_ID']

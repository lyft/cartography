import logging

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_tenant_id(credentials):
    return credentials.get_tenant_id()


def load_azure_tenant(neo4j_session, tenant_id, current_user, azure_update_tag, common_job_parameters):
    query = """
    MERGE (at:AzureTenant{id: {TENANT_ID}})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = {azure_update_tag}
    WITH at
    MERGE (ap:AzurePrincipal{email: {CURRENT_USER}})
    ON CREATE SET ap.firstseen = timestamp(), ap.type = 'AZURE'
    SET ap.lastupdated = {azure_update_tag}
    WITH at, ap
    MERGE (at)-[r:RESOURCE]->(ap)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag};
    """
    neo4j_session.run(
        query,
        TENANT_ID=tenant_id,
        CURRENT_USER=current_user,
        azure_update_tag=azure_update_tag,
    )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_tenant_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, tenant_id, current_user, azure_update_tag, common_job_parameters):
    load_azure_tenant(neo4j_session, tenant_id, current_user, azure_update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

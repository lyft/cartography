import logging
from typing import Dict
from typing import List

import neo4j

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import SubscriptionClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def list_tenants(credentials: Credentials) -> List[Dict]:
    try:
        # Create the client
        client = SubscriptionClient(credentials.arm_credentials)

        # Get all the accessible tenants
        tenants_list = list(client.tenants.list())

    except HttpResponseError as e:
        logger.error(
            f'failed to fetch tenants for the credentials \
            The provided credentials do not have access to any subscriptions - \
            {e}',
        )

        return []

    tenants = []
    for tenant in tenants_list:
        tenants.append({
            'id': tenant.id,
            'tenantId': tenant.tenant_id,
            'tenantCategory': tenant.tenant_category,
            'tenantType': tenant.tenant_type,
            'displayName': tenant.display_name,
            'country': tenant.country,
            'countryCode': tenant.country_code,
            'defaultDomain': tenant.default_domain,
        })

    return tenants


def get_active_tenant(credentials: Credentials) -> Dict:
    # Fetch current tenant
    tenants = list_tenants(credentials)
    tenant_obj = list(filter(lambda t: t['tenantId'] == credentials.get_tenant_id(), tenants))

    return tenant_obj[0]


def get_tenant_id(credentials: Credentials) -> str:
    return credentials.get_tenant_id()


def load_azure_tenant(
    neo4j_session: neo4j.Session, tenant_obj: Dict, current_user: str, update_tag: int, common_job_parameters: Dict
) -> None:
    query = """
    MERGE (w:CloudanixWorkspace{id: $workspaceId})
    SET w.lastupdated = $update_tag
    WITH w
    MERGE (at:AzureTenant{id: $tenantId})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = $update_tag,
    at.path = $id,
    at.tenantCategory = $tenantCategory,
    at.tenantType = $tenantType,
    at.displayName = $displayName,
    at.country = $country,
    at.countryCode = $countryCode,
    at.defaultDomain = $defaultDomain
    WITH w, at
    MERGE (w)-[o:OWNER]->(at)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $update_tag
    WITH at
    MERGE (ap:AzurePrincipal{id: $userEmail})
    ON CREATE SET ap.email = $userEmail, ap.firstseen = timestamp()
    SET ap.lastupdated = $update_tag,
    ap.name=$userName, ap.userid=$userId
    WITH at, ap
    MERGE (at)-[r:RESOURCE]->(ap)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag;
    """
    neo4j_session.run(
        query,
        workspaceId=common_job_parameters['WORKSPACE_ID'],
        id=tenant_obj['id'],
        tenantId=tenant_obj['tenantId'],
        tenantCategory=tenant_obj['tenantCategory'],
        tenantType=tenant_obj['tenantType'],
        displayName=tenant_obj['displayName'],
        country=tenant_obj['country'],
        countryCode=tenant_obj['countryCode'],
        defaultDomain=tenant_obj['defaultDomain'],
        userEmail=current_user['email'],
        userId=current_user.get('id'),
        userName=current_user.get('name'),
        update_tag=update_tag,
    )


def cleanup(neo4j_session: neo4j.Session, tenant_obj: Dict, common_job_parameters: Dict) -> None:
    common_job_parameters['AZURE_TENANT_ID'] = tenant_obj['tenantId']

    run_cleanup_job('azure_tenant_cleanup.json', neo4j_session, common_job_parameters)

    del common_job_parameters["AZURE_TENANT_ID"]


@timeit
def sync(
    neo4j_session: neo4j.Session, tenant_obj: Dict, current_user: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    load_azure_tenant(neo4j_session, tenant_obj, current_user, update_tag, common_job_parameters)
    cleanup(neo4j_session, tenant_obj, common_job_parameters)
    common_job_parameters['Object_ID'] = current_user['id']

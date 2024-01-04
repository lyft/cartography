import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import get_azure_resource_group_name
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_aks(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_aks_tx, subscription_id, data_list, update_tag)



@timeit
def get_client(credentials: Credentials, subscription_id: str) -> ContainerServiceClient:
    client = ContainerServiceClient(credentials, subscription_id)
    return client



@timeit
def get_aks_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        aks_list = list(map(lambda x: x.as_dict(), client.managed_clusters.list()))
        aks_data = []
        for aks in aks_list:
            aks['resource_group'] = get_azure_resource_group_name(aks.get('id'))
            aks['publicNetworkAccess'] = aks.get('properties', {}).get('public_network_access', 'Disabled')
            aks['consolelink'] = azure_console_link.get_console_link(
                id=aks['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                aks_data.append(aks)
            else:
                if aks.get('location') in regions or aks.get('location') == 'global':
                    aks_data.append(aks)
        return aks_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving AKS - {e}")
        return []


def _load_aks_tx(tx: neo4j.Transaction, subscription_id: str, aks_list: List[Dict], update_tag: int) -> None:
    ingest_aks = """
    UNWIND $aks_list AS aks
    MERGE (a:AzureCluster{id: aks.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = aks.type,
    a.location = aks.location,
    a.region = aks.location,
    a.publicNetworkAccess = aks.publicNetworkAccess,
    a.consolelink = aks.consolelink,
    a.resourcegroup = aks.resource_group
    SET a.lastupdated = $update_tag,
    a.name = aks.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_aks,
        aks_list=aks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for aks in aks_list:
        resource_group=get_azure_resource_group_name(aks.get('id'))
        _attach_resource_group_aks(tx,aks['id'],resource_group,update_tag)

def _attach_resource_group_aks(tx: neo4j.Transaction, aks_id:str,resource_group:str ,update_tag: int) -> None:
    ingest_aks_resource = """
    MATCH (a:AzureCluster{id: $aks_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[res:RESOURCE_GROUP]->(rg)
    ON CREATE SET res.firstseen = timestamp()
    SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_aks_resource,
        aks_id=aks_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )
    

def cleanup_aks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_aks_cleanup.json', neo4j_session, common_job_parameters)


def sync_aks(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    aks_list = get_aks_list(credentials, subscription_id, regions, common_job_parameters)

    load_aks(neo4j_session, subscription_id, aks_list, update_tag)
    cleanup_aks(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list


) -> None:
    logger.info("Syncing AKS for subscription '%s'.", subscription_id)

    sync_aks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    
import logging
from typing import Dict
from typing import List

import neo4j

from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerservice import ContainerServiceClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def get_client(credentials: Credentials, subscription_id: str) -> ContainerServiceClient:
    client = ContainerServiceClient(credentials, subscription_id)
    return client

@timeit
def get_aks_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        aks_list = list(map(lambda x: x.as_dict(), client.managed_clusters.list()))

        for aks in aks_list:
            x = aks['id'].split('/')
            aks['resource_group'] = x[x.index('resourcegroups') + 1]

        return aks_list[0]["name"]

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving functions - {e}")
        return []

def load_aks(neo4j_session: neo4j.Session, subscription_id: str, aks_list: List[Dict], update_tag: int) -> None:
    ingest_aks = """
    UNWIND {akss} AS aks
    MERGE (a:AzureCluster{id: aks.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = aks.type,
    a.location = aks.location,
    a.resourcegroup = aks.resource_group
    SET a.lastupdated = {update_tag}, 
    a.name = aks.name
    WITH a
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_aks,
        akss=aks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )

def cleanup_aks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_aks_cleanup.json', neo4j_session, common_job_parameters)


def sync_aks(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    aks_list = get_aks_list(credentials, subscription_id)
    load_aks(neo4j_session, subscription_id, aks_list, update_tag)
    cleanup_aks(neo4j_session, common_job_parameters)



@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing AKS for subscription '%s'.", subscription_id)

    sync_aks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)

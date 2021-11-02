import logging
from typing import Dict
from typing import List

import neo4j

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def get_network_client(credentials: Credentials, subscription_id: str) -> NetworkManagementClient:
    client = NetworkManagementClient(credentials, subscription_id)
    return client


def get_resource_group_client(credentials: Credentials, subscription_id: str) -> ResourceManagementClient:
    client = ResourceManagementClient(credentials, subscription_id)
    return client


def get_resource_groups_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_resource_group_client(credentials, subscription_id)
        resource_group_list = list(map(lambda x: x.as_dict(), client.resource_groups.list()))

        return resource_group_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving resource group - {e}")
        return []


@timeit
def get_networks_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        resource_group_list=get_resource_groups_list(credentials, subscription_id)
        networks_list=[]

        for resource_group in resource_group_list:
            client = get_network_client(credentials, subscription_id)
            networks_list = networks_list + list(map(lambda x: x.as_dict(), client.virtual_networks.list(resource_group["name"])))
        for net in networks_list:
            x = net['id'].split('/')
            net['resource_group'] = x[x.index('resourceGroups') + 1]   
        return networks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network - {e}")
        return []


def load_networks(neo4j_session: neo4j.Session, subscription_id: str, networks_list: List[Dict], update_tag: int) -> None:
    ingest_net = """
    UNWIND {networks} AS network
    MERGE (n:AzureNetwork{id: network.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = network.type,
    n.location = network.location,
    n.resourcegroup = network.resource_group
    SET n.lastupdated = {update_tag}, 
    n.name = network.name, 
    n.resource_guid = network.resource_guid,
    n.provisioning_state=network.provisioning_state, 
    n.enable_ddos_protection=network.enable_ddos_protection,
    n.etag=network.etag 
    WITH n
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_net,
        networks=networks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )

def cleanup_network(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_cleanup.json', neo4j_session, common_job_parameters)


def sync_network(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_list = get_networks_list(credentials, subscription_id)
    load_networks(neo4j_session, subscription_id, networks_list, update_tag)
    cleanup_network(neo4j_session, common_job_parameters)



@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing networks for subscription '%s'.", subscription_id)

    sync_network(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)


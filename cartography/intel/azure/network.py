import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_networks(session: neo4j.Session, subscription_id: str,
                  data_list: List[Dict[str, Optional[str]]],
                  update_tag: int) -> None:
    session.write_transaction(_load_networks_tx, subscription_id, data_list, update_tag)


def load_networks_subnets(session: neo4j.Session, data_list: List[Dict[str, Optional[str]]], update_tag: int) -> None:
    session.write_transaction(_load_networks_subnets_tx, data_list, update_tag)


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
        logger.warning(f"Error while retrieving resource groups - {e}")
        return []


@timeit
def get_networks_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_network_client(credentials, subscription_id)
        resource_groups_list = get_resource_groups_list(credentials, subscription_id)
        networks_list = []

        for resource_group in resource_groups_list:
            networks_list = networks_list + list(map(lambda x: x.as_dict(), client.virtual_networks.list(resource_group["name"])))

        for network in networks_list:
            x = network['id'].split('/')
            network['resource_group'] = x[x.index('resourceGroups') + 1]
        return networks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving networks - {e}")
        return []


def _load_networks_tx(tx: neo4j.Transaction, subscription_id: str, networks_list: List[Dict], update_tag: int) -> None:
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

    tx.run(
        ingest_net,
        networks=networks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_networks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_cleanup.json', neo4j_session, common_job_parameters)


def sync_networks(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_list = get_networks_list(credentials, subscription_id)
    load_networks(neo4j_session, subscription_id, networks_list, update_tag)
    cleanup_networks(neo4j_session, common_job_parameters)


@timeit
def get_networks_subnets_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_network_client(credentials, subscription_id)
        networks_list = get_networks_list(credentials, subscription_id)
        networks_subnets_list = []
        for network in networks_list:
            networks_subnets_list = networks_subnets_list + list(map(lambda x: x.as_dict(), client.subnets.list(resource_group_name=network['resource_group'], virtual_network_name=network["name"])))

        for subnet in networks_subnets_list:
            x = subnet['id'].split('/')
            subnet['resource_group'] = x[x.index('resourceGroups') + 1]
            subnet['network_id'] = subnet['id'][:subnet['id'].
                                                index("/subnets")]
            subnet['type'] = "Microsoft.Network/Subnets"
        return networks_subnets_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving subnets - {e}")
        return []


def _load_networks_subnets_tx(
    tx: neo4j.Transaction,
    networks_subnets_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_network_subnet = """
    UNWIND {networks_subnets_list} as subnet
    MERGE (n:AzureNetworkSubnet{id: subnet.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = subnet.type
    SET n.name = subnet.name,
    n.lastupdated = {azure_update_tag},
    n.resource_group_name=subnet.resource_group,
    n.href=subnet.private_endpoint_network_policies,
    n.language=subnet.private_link_service_network_policies,
    n.is_disabled=subnet.etag
    WITH n, subnet
    MATCH (s:AzureNetwork{id: subnet.network_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    tx.run(
        ingest_network_subnet,
        networks_subnets_list=networks_subnets_list,
        azure_update_tag=update_tag,
    )


def cleanup_networks_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_subnets_cleanup.json', neo4j_session, common_job_parameters)


def sync_networks_subnets(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_subnets_list = get_networks_subnets_list(credentials, subscription_id)
    load_networks_subnets(neo4j_session, networks_subnets_list, update_tag)
    cleanup_networks_subnets(neo4j_session, common_job_parameters)


@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing networks for subscription '%s'.", subscription_id)

    sync_networks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_networks_subnets(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)

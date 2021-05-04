import logging
from azure.mgmt.compute import ComputeManagementClient
from cartography.util import get_optional_value
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_client(credentials, subscription_id):
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def get_security_group_list(credentials, subscription_id):
    client = get_client(credentials, subscription_id)
    security_groups = list(client.network_security_group.list_all())
    return security_groups


def load_security_group_info(neo4j_session, subscription_id, groups, azure_update_tag, common_job_parameters):
    ingest_security_group = """
    MERGE (group:AzureSecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.name = {GroupName}, group.location = {location},
    group.lastupdated = {azure_update_tag}
    WITH group
    MATCH (aa:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for group in groups:
        group_id = group["id"]

        neo4j_session.run(
            ingest_security_group,
            GroupId=group_id,
            GroupName=group.get("name"),
            location=group.get('location'),
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag,
        )


def cleanup_network_security_group(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_network_security_group_cleanup.json', neo4j_session, common_job_parameters)


def get_virtual_network_group(credentials, subscription_id):
    client = get_client(credentials, subscription_id)
    virtual_networks = list(client.virtual_network.list_all())
    return virtual_networks


def load_virtual_network_data(neo4j_session, credentials, virtual_network_list, subscription_id, azure_update_tag, common_job_parameters):
    ingest_virtual_network = """
    MERGE (virtualNetwork:AzureVirtualNetwork{id: {id}})
    ON CREATE SET virtualNetwork.firstseen = timestamp(), virtualNetwork.vpcid ={id}
    SET virtualNetwork.name= {name},
    virtualNetwork.type = {type},
    virtualNetwork.location = {location},
    virtualNetwork.etag= {etag},
    virtualNetwork.lastupdated = {azure_update_tag}
    WITH virtualNetwork
    MATCH (owner:AzureSubscription{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(virtualNetwork)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""

    for virtualNetwork in virtual_network_list:
        neo4j_session.run(
            ingest_virtual_network,
            name=virtualNetwork.get('name'),
            id=virtualNetwork.get('id'),
            type=virtualNetwork.get('type'),
            location=virtualNetwork.get('location'),
            etag=virtualNetwork.get('etag'),
            virtualNetworkPeerings=virtualNetwork['properties']['virtualNetworkPeerings'],
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag,
        )


def cleanup_virtual_network(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_virtual_network_cleanup.json', neo4j_session, common_job_parameters)


def get_network_interface_group(credentials, subscription_id):
    client = get_client(credentials, subscription_id)
    network_interface_list = list(client.network_interface.list_all())
    return network_interface_list


def load_network_interface_data(neo4j_session, subscription_id, network_interface_list, azure_update_tag, common_job_parameters):
    ingest_network_interface = """
    MERGE (NetworkInterface:AzureNetworkInterface{id: {id}})
    ON CREATE SET NetworkInterface.firstseen = timestamp(), virtualNetwork.id ={id}
    SET NetworkInterface.name= {name},
    NetworkInterface.type = {type},
    NetworkInterface.location = {location},
    NetworkInterface.etag= {etag},
    NetworkInterface.macAddress= {macAddress},
    NetworkInterface.networkSecurityGroupId={networkSecurityGroupId}
    NetworkInterface.lastupdated = {azure_update_tag}
    WITH NetworkInterface
    MATCH (owner:AzureSubscription{id: {subscription_id}})
    MERGE (owner)-[r:RESOURCE]->(NetworkInterface)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}"""

    for networkInterface in network_interface_list:
        neo4j_session.run(
            ingest_network_interface,
            name=networkInterface.get('name'),
            id=networkInterface.get('id'),
            type=networkInterface.get('type'),
            location=networkInterface.get('location'),
            etag=networkInterface.get('etag'),
            macAddress=networkInterface.get('macAddress'),
            networkSecurityGroupId=get_optional_value(networkInterface, ['properties', 'macAddress', 'networkSecurityGroup', 'id']),
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag,
        )


def cleanup_network_interface(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_import_network_interface_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_interface(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    network_interface_list = get_network_interface_group(credentials, subscription_id)
    load_network_interface_data(neo4j_session, subscription_id, network_interface_list, sync_tag, common_job_parameters)
    cleanup_network_interface(neo4j_session, common_job_parameters)


def sync_virtual_network(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    virtual_network_list = get_virtual_network_group(credentials, subscription_id)
    load_virtual_network_data(neo4j_session, credentials, virtual_network_list, subscription_id, sync_tag, common_job_parameters)
    cleanup_virtual_network(neo4j_session, common_job_parameters)


def sync_network_security_group(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    groups = get_security_group_list(credentials, subscription_id)
    load_security_group_info(neo4j_session, subscription_id, groups, sync_tag, common_job_parameters)
    cleanup_network_security_group(neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, location, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_network(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_network_interface(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)
    sync_network_security_group(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)

import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.network import NetworkManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_networks(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_networks_tx, subscription_id, data_list, update_tag)


def load_networks_subnets(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_networks_subnets_tx, data_list, update_tag)


def load_network_routetables(
        session: neo4j.Session,
        subscription_id: str,
        data_list: List[Dict],
        update_tag: int,
) -> None:
    session.write_transaction(_load_network_routetables_tx, subscription_id, data_list, update_tag)


def load_network_routes(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_network_routes_tx, data_list, update_tag)


def load_network_security_groups(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.write_transaction(_load_network_security_groups_tx, subscription_id, data_list, update_tag)


def load_network_security_rules(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_network_security_rules_tx, data_list, update_tag)


def load_public_ip_addresses(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.write_transaction(_load_public_ip_addresses_tx, subscription_id, data_list, update_tag)


def load_network_interfaces(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.write_transaction(_load_network_interfaces_tx, subscription_id, data_list, update_tag)


def load_public_ip_network_interfaces_relationship(session: neo4j.Session, interface_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_public_ip_network_interfaces_relationship, interface_id, data_list, update_tag)


def load_usages(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_usages_tx, data_list, update_tag)


@timeit
def get_network_client(credentials: Credentials, subscription_id: str) -> NetworkManagementClient:
    client = NetworkManagementClient(credentials, subscription_id)
    return client


@timeit
def get_networks_list(client: NetworkManagementClient) -> List[Dict]:
    try:
        networks_list = list(map(lambda x: x.as_dict(), client.virtual_networks.list_all()))

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
    n.region = network.location,
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
    client = get_network_client(credentials, subscription_id)
    networks_list = get_networks_list(client)
    load_networks(neo4j_session, subscription_id, networks_list, update_tag)
    cleanup_networks(neo4j_session, common_job_parameters)
    sync_networks_subnets(neo4j_session, networks_list, client, update_tag, common_job_parameters)
    sync_network_routetables(neo4j_session, client, subscription_id, update_tag, common_job_parameters)
    sync_public_ip_addresses(neo4j_session, client, subscription_id, update_tag, common_job_parameters)
    sync_network_interfaces(neo4j_session, client, subscription_id, update_tag, common_job_parameters)
    sync_usages(neo4j_session, networks_list, client, update_tag, common_job_parameters)


@timeit
def get_networks_subnets_list(networks_list: List[Dict], client: NetworkManagementClient) -> List[Dict]:
    try:
        networks_subnets_list: List[Dict] = []
        for network in networks_list:
            subnets_list = list(
                map(
                    lambda x: x.as_dict(), client.subnets.list(
                        resource_group_name=network['resource_group'], virtual_network_name=network["name"],
                    ),
                ),
            )

            for subnet in subnets_list:
                x = subnet['id'].split('/')
                subnet['resource_group'] = x[x.index('resourceGroups') + 1]
                subnet['network_id'] = subnet['id'][:subnet['id'].index("/subnets")]
                subnet['type'] = "Microsoft.Network/Subnets"
                subnet['location'] = network.get('location', 'global')
                subnet['network_security_group_id'] = subnet.get('network_security_group', {}).get('id', None)
            networks_subnets_list.extend(subnets_list)
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
    n.region= subnet.location,
    n.resource_group_name=subnet.resource_group,
    n.private_endpoint_network_policies=subnet.private_endpoint_network_policies,
    n.private_link_service_network_policies=subnet.private_link_service_network_policies,
    n.etag=subnet.etag
    WITH n, subnet
    MATCH (s:AzureNetwork{id: subnet.network_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    WITH n, subnet
    MATCH (sg:AzureNetworkSecurityGroup{id: subnet.network_security_group_id})
    MERGE (n)-[sgr:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET sgr.firstseen = timestamp()
    SET sgr.lastupdated = {azure_update_tag}
    """

    tx.run(
        ingest_network_subnet,
        networks_subnets_list=networks_subnets_list,
        azure_update_tag=update_tag,
    )


def cleanup_networks_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_subnets_cleanup.json', neo4j_session, common_job_parameters)


def sync_networks_subnets(
    neo4j_session: neo4j.Session, networks_list: List[Dict],
    client: NetworkManagementClient, update_tag: int, common_job_parameters: Dict,
) -> None:
    networks_subnets_list = get_networks_subnets_list(networks_list, client)
    load_networks_subnets(neo4j_session, networks_subnets_list, update_tag)
    cleanup_networks_subnets(neo4j_session, common_job_parameters)


def get_network_routetables_list(client: NetworkManagementClient) -> List[Dict]:
    try:
        network_routetables_list = list(map(lambda x: x.as_dict(), client.route_tables.list_all()))

        for routetable in network_routetables_list:
            x = routetable['id'].split('/')
            routetable['resource_group'] = x[x.index('resourceGroups') + 1]
        return network_routetables_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving routetables - {e}")
        return []


def _load_network_routetables_tx(
    tx: neo4j.Transaction, subscription_id: str, network_routetables_list: List[Dict], update_tag: int,
) -> None:
    ingest_routetables = """
    UNWIND {network_routetables_list} AS routetable
    MERGE (n:AzureRouteTable{id: routetable.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = routetable.type,
    n.location = routetable.location,
    n.region = routetable.location,
    n.resourcegroup = routetable.resource_group
    SET n.lastupdated = {update_tag},
    n.name = routetable.name,
    n.etag=routetable.etag
    WITH n
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_routetables,
        network_routetables_list=network_routetables_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_network_routetables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_routetables_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_routetables(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    network_routetables_list = get_network_routetables_list(client)
    load_network_routetables(neo4j_session, subscription_id, network_routetables_list, update_tag)
    cleanup_network_routetables(neo4j_session, common_job_parameters)
    sync_network_routes(neo4j_session, network_routetables_list, client, update_tag, common_job_parameters)


@timeit
def get_network_routes_list(network_routetables_list: List[Dict], client: NetworkManagementClient) -> List[Dict]:
    try:
        network_routes_list: List[Dict] = []
        for routetable in network_routetables_list:
            routes_list = list(
                map(
                    lambda x: x.as_dict(), client.routes.list(
                        resource_group_name=routetable['resource_group'], route_table_name=routetable['name'],
                    ),
                ),
            )

            for route in routes_list:
                x = route['id'].split('/')
                route['resource_group'] = x[x.index('resourceGroups') + 1]
                route['routetable_id'] = route['id'][:route['id'].index("/routes")]
                route['location'] = routetable.get('location', 'global')
            network_routes_list.extend(routes_list)
        return network_routes_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving routes - {e}")
        return []


def _load_network_routes_tx(
    tx: neo4j.Transaction,
    network_routes_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_network_route = """
    UNWIND {network_routes_list} as route
    MERGE (n:AzureNetworkRoute{id: route.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = route.type
    SET n.name = route.name,
    n.region= route.location,
    n.lastupdated = {azure_update_tag},
    n.etag=route.etag
    WITH n, route
    MATCH (s:AzureRouteTable{id: route.routetable_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    tx.run(
        ingest_network_route,
        network_routes_list=network_routes_list,
        azure_update_tag=update_tag,
    )


def cleanup_network_routes(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_routes_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_routes(
    neo4j_session: neo4j.Session, network_routetables_list: List[Dict],
    client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_routes_list = get_network_routes_list(network_routetables_list, client)
    load_network_routes(neo4j_session, networks_routes_list, update_tag)
    cleanup_network_routes(neo4j_session, common_job_parameters)


def get_network_security_groups_list(client: NetworkManagementClient) -> List[Dict]:
    try:
        network_security_groups_list = list(map(lambda x: x.as_dict(), client.network_security_groups.list_all()))

        for network in network_security_groups_list:
            x = network['id'].split('/')
            network['resource_group'] = x[x.index('resourceGroups') + 1]
        return network_security_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network_security_groups - {e}")
        return []


def _load_network_security_groups_tx(
    tx: neo4j.Transaction, subscription_id: str, network_security_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_network = """
    UNWIND {network_security_groups_list} AS network
    MERGE (n:AzureNetworkSecurityGroup{id: network.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = network.type,
    n.location = network.location,
    n.region = network.location,
    n.resourcegroup = network.resource_group
    SET n.lastupdated = {update_tag},
    n.name = network.name,
    n.etag=network.etag
    WITH n
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_network,
        network_security_groups_list=network_security_groups_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_network_security_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_security_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_security_groups(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    network_security_groups_list = get_network_security_groups_list(client)
    load_network_security_groups(neo4j_session, subscription_id, network_security_groups_list, update_tag)
    cleanup_network_security_groups(neo4j_session, common_job_parameters)
    sync_network_security_rules(neo4j_session, network_security_groups_list, client, update_tag, common_job_parameters)


@timeit
def get_network_security_rules_list(
    network_security_groups_list: List[Dict], client: NetworkManagementClient,
) -> List[Dict]:
    try:
        network_security_rules_list: List[Dict] = []
        for security_group in network_security_groups_list:
            security_rules_list = security_group.get('security_rules', [])
            for rule in security_rules_list:
                x = rule['id'].split('/')
                rule['resource_group'] = x[x.index('resourceGroups') + 1]
                rule['security_group_id'] = rule['id'][:rule['id'].index("/securityRules")]
                rule['location'] = rule.get('location', 'global')
                rule['access'] = rule.get('access', 'Deny')
                rule['source_port_range'] = rule.get('source_port_range', None)
                rule['source_address_prefix'] = rule.get('source_address_prefix', None)
                rule['protocol'] = rule.get('protocol', None)
                rule['direction'] = rule.get('direction', None)
                rule['destination_port_ranges'] = rule.get(
                    'properties', {}).get('destination_port_ranges', None)
                rule['destination_address_prefix'] = rule.get('destination_address_prefix', None)
            network_security_rules_list.extend(security_rules_list)
        return network_security_rules_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network_security_rules - {e}")
        return []


def _load_network_security_rules_tx(
    tx: neo4j.Transaction,
    network_security_rules_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_network_rule = """
    UNWIND {network_security_rules_list} as rule
    MERGE (n:AzureNetworkSecurityRule{id: rule.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.access = rule.access,
    n.source_port_range = rule.source_port_range,
    n.protocol = rule.protocol,
    n.direction = rule.direction,
    n.destination_address_prefix = rule.destination_address_prefix,
    n.source_address_prefix = rule.source_address_prefix,
    n.destination_port_ranges = rule.destination_port_ranges,
    n.type = rule.type
    SET n.name = rule.name,
    n.region= rule.location,
    n.lastupdated = {azure_update_tag},
    n.etag=rule.etag
    WITH n, rule
    MATCH (s:AzureNetworkSecurityGroup{id: rule.security_group_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    tx.run(
        ingest_network_rule,
        network_security_rules_list=network_security_rules_list,
        azure_update_tag=update_tag,
    )


def cleanup_network_security_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_security_rules_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_security_rules(
    neo4j_session: neo4j.Session, network_security_groups_list: List[Dict],
    client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    network_security_rules_list = get_network_security_rules_list(network_security_groups_list, client)
    load_network_security_rules(neo4j_session, network_security_rules_list, update_tag)
    cleanup_network_security_rules(neo4j_session, common_job_parameters)


def get_public_ip_addresses_list(client: NetworkManagementClient) -> List[Dict]:
    try:
        public_ip_addresses_list = list(map(lambda x: x.as_dict(), client.public_ip_addresses.list_all()))
        return public_ip_addresses_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving public_ip_addresses - {e}")
        return []


def _load_public_ip_addresses_tx(
    tx: neo4j.Transaction, subscription_id: str, public_ip_addresses_list: List[Dict], update_tag: int,
) -> None:
    ingest_address = """
    UNWIND {public_ip_addresses_list} AS address
    MERGE (n:AzurePublicIPAddress{id: address.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = address.type,
    n.location = address.location,
    n.region = address.location
    SET n.lastupdated = {update_tag},
    n.name = address.name,
    n.etag=address.etag
    WITH n
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_address,
        public_ip_addresses_list=public_ip_addresses_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_public_ip_addresses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_public_ip_addresses_cleanup.json', neo4j_session, common_job_parameters)


def sync_public_ip_addresses(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    public_ip_addresses_list = get_public_ip_addresses_list(client)
    load_public_ip_addresses(neo4j_session, subscription_id, public_ip_addresses_list, update_tag)
    cleanup_public_ip_addresses(neo4j_session, common_job_parameters)


def get_network_interfaces_list(client: NetworkManagementClient) -> List[Dict]:
    try:
        network_interfaces_list = list(map(lambda x: x.as_dict(), client.network_interfaces.list_all()))
        interfaces_list = []
        for interface in network_interfaces_list:
            interface['public_ip_address'] = []
            for conf in interface.get('ip_configurations', []):
                interface['public_ip_address'].append(
                    {'public_ip_id': conf.get('public_ip_address', {}).get('id', None)})
            interfaces_list.append(interface)
        return interfaces_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving network interface - {e}")
        return []


def _load_network_interfaces_tx(
    tx: neo4j.Transaction, subscription_id: str, network_interfaces_list: List[Dict], update_tag: int,
) -> None:
    ingest_interface = """
    UNWIND {network_interfaces_list} AS interface
    MERGE (n:AzureNetworkInterface{id: interface.id})
    ON CREATE SET n.firstseen = timestamp(),
    n.type = interface.type,
    n.location = interface.location,
    n.region = interface.location
    SET n.lastupdated = {update_tag},
    n.name = interface.name
    WITH n, interface
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    WITH n, interface
    MATCH (sg:AzureNetworkSecurityGroup{id: interface.network_security_group.id})
    MERGE (n)-[sgr:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET sgr.firstseen = timestamp()
    SET sgr.lastupdated = {update_tag}
    """

    tx.run(
        ingest_interface,
        network_interfaces_list=network_interfaces_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_network_interfaces(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_network_interfaces_cleanup.json', neo4j_session, common_job_parameters)


def sync_network_interfaces(
    neo4j_session: neo4j.Session, client: NetworkManagementClient, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    network_interfaces_list = get_network_interfaces_list(client)
    load_network_interfaces(neo4j_session, subscription_id, network_interfaces_list, update_tag)
    cleanup_network_interfaces(neo4j_session, common_job_parameters)
    for interface in network_interfaces_list:
        load_public_ip_network_interfaces_relationship(neo4j_session, interface.get(
            'id'), interface.get('public_ip_address', []), update_tag)


def _load_public_ip_network_interfaces_relationship(tx: neo4j.Transaction, interface_id: str, data_list: List[Dict], update_tag: int) -> None:
    ingest_ip_ni = """
    UNWIND {ip_list} AS public_ip
    MATCH (ip:AzurePublicIPAddress{id: public_ip.public_ip_id})
    WITH ip
    MATCH (i:AzureNetworkInterface{id: {interface_id}})
    MERGE (i)-[r:MEMBER_PUBLIC_IP_ADDRESS]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """
    tx.run(
        ingest_ip_ni,
        ip_list=data_list,
        interface_id=interface_id,
        update_tag=update_tag,
    )


@timeit
def get_usages_list(networks_list: List[Dict], client: NetworkManagementClient) -> List[Dict]:
    try:
        usages_list: List[Dict] = []
        for network in networks_list:
            usages = list(
                map(
                    lambda x: x.as_dict(), client.virtual_networks.list_usage(
                        resource_group_name=network['resource_group'], virtual_network_name=network['name'],
                    ),
                ),
            )

            for usage in usages:
                usage['network_id'] = usage['id'][:usage['id'].index("/subnets")]
                usage['location'] = network.get('location', 'global')
            usages_list.extend(usages)
        return usages_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving usages - {e}")
        return []


def _load_usages_tx(
    tx: neo4j.Transaction,
    usages_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_usages = """
    UNWIND {usages_list} as usage
    MERGE (n:AzureNetworkUsage{id: usage.id})
    ON CREATE SET n.firstseen = timestamp()
    SET n.currentValue = usage.currentValue,
    n.region= usage.location,
    n.lastupdated = {azure_update_tag},
    n.limit=usage.limit,
    n.unit=usage.unit
    WITH n, usage
    MATCH (s:AzureNetwork{id: usage.network_id})
    MERGE (s)-[r:CONTAIN]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    tx.run(
        ingest_usages,
        location="global",
        usages_list=usages_list,
        azure_update_tag=update_tag,
    )


def cleanup_usages(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_networks_usages_cleanup.json', neo4j_session, common_job_parameters)


def sync_usages(
    neo4j_session: neo4j.Session, networks_list: List[Dict], client: NetworkManagementClient, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    networks_usages_list = get_usages_list(networks_list, client)
    load_usages(neo4j_session, networks_usages_list, update_tag)
    cleanup_usages(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing networks for subscription '%s'.", subscription_id)

    client = get_network_client(credentials, subscription_id)
    sync_network_security_groups(neo4j_session, client, subscription_id, update_tag, common_job_parameters)
    sync_networks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)

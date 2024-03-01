from cartography.intel.azure import network
from cartography.util import run_analysis_job
from tests.data.azure.network import DESCRIBE_NETWORKROUTE
from tests.data.azure.network import DESCRIBE_NETWORKS
from tests.data.azure.network import DESCRIBE_NETWORKSECURITYGROUPS
from tests.data.azure.network import DESCRIBE_NETWORKSECURITYRULES
from tests.data.azure.network import DESCRIBE_NETWORKSUBNETS
from tests.data.azure.network import DESCRIBE_NETWORKUSAGES
from tests.data.azure.network import DESCRIBE_PUBLICIPADDRESSES
from tests.data.azure.network import DESCRIBE_ROUTETABLE

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '123'
TEST_TENANT_ID = '123'


def test_load_networks(neo4j_session):
    network.load_networks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetwork) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_networks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureNetwork) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_network_subnets(neo4j_session):
    network.load_networks_subnets(
        neo4j_session,
        DESCRIBE_NETWORKSUBNETS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkSubnet) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_subnet_relationships(neo4j_session):
    network.load_networks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKS,
        TEST_UPDATE_TAG,
    )

    network.load_networks_subnets(
        neo4j_session,
        DESCRIBE_NETWORKSUBNETS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureNetwork)-[:CONTAIN]->(n2:AzureNetworkSubnet) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_routetables(neo4j_session):
    network.load_network_routetables(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_ROUTETABLE,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureRouteTable) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_routetable_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_network_routetables(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_ROUTETABLE,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureRouteTable) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_network_routes(neo4j_session):
    network.load_network_routes(
        neo4j_session,
        DESCRIBE_NETWORKROUTE,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1/routes1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2/routes2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkRoute) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_route_relationships(neo4j_session):
    network.load_network_routetables(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_ROUTETABLE,
        TEST_UPDATE_TAG,
    )

    network.load_network_routes(
        neo4j_session,
        DESCRIBE_NETWORKROUTE,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable1/routes1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            routeTables/TestRoutetable2/routes2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureRouteTable)-[:CONTAIN]->(n2:AzureNetworkRoute) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_network_security_groups(neo4j_session):
    network.load_network_security_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKSECURITYGROUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkSecurityGroup) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_security_group_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_network_security_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKSECURITYGROUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureNetworkSecurityGroup) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_network_security_rule(neo4j_session):
    network.load_network_security_rules(
        neo4j_session,
        DESCRIBE_NETWORKSECURITYRULES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1/securityRules/rule1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2/securityRules/rule2",
        '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2/securityRules/rule3',
        '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2/securityRules/rule4',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkSecurityRule) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_security_rule_relationships(neo4j_session):
    network.load_network_security_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKSECURITYGROUPS,
        TEST_UPDATE_TAG,
    )

    network.load_network_security_rules(
        neo4j_session,
        DESCRIBE_NETWORKSECURITYRULES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup1/securityRules/rule1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            networkSecurityGroups/Testgroup2/securityRules/rule2",
        ),

        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup2',
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup2/securityRules/rule3',
        ),
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup1',
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup2/securityRules/rule4',
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureNetworkSecurityGroup)-[:CONTAIN]->(n2:AzureNetworkSecurityRule) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_public_ip_addresses(neo4j_session):
    network.load_public_ip_addresses(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_PUBLICIPADDRESSES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzurePublicIPAddress) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_public_ip_address_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_public_ip_addresses(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_PUBLICIPADDRESSES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            publicIPAddresses/ip2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzurePublicIPAddress) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_network_usages(neo4j_session):
    network.load_usages(
        neo4j_session,
        DESCRIBE_NETWORKUSAGES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkUsage) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_network_usage_relationships(neo4j_session):
    network.load_networks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKS,
        TEST_UPDATE_TAG,
    )

    network.load_usages(
        neo4j_session,
        DESCRIBE_NETWORKUSAGES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork1/subnets/subnet1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/\
            virtualNetworks/TestNetwork2/subnets/subnet2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureNetwork)-[:CONTAIN]->(n2:AzureNetworkUsage) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_network_security_group_analysis(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})<-[:RESOURCE]-(:AzureTenant{id: $AZURE_TENANT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        AZURE_TENANT_ID=TEST_TENANT_ID,
        WORKSPACE_ID=TEST_WORKSPACE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    network.load_network_security_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_NETWORKSECURITYGROUPS,
        TEST_UPDATE_TAG,
    )

    network.load_network_security_rules(
        neo4j_session,
        DESCRIBE_NETWORKSECURITYRULES,
        TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        "AZURE_TENANT_ID": TEST_TENANT_ID,
    }

    run_analysis_job(
        'azure_network_security_group_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    expected_nodes = {
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup1',
            'direct_ipv4,public_icmp',
        ),
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/            '
            'networkSecurityGroups/Testgroup2',
            'inbound_public_ports',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureNetworkSecurityGroup{exposed_internet: true}) RETURN r.id, r.exposed_internet_type;
        """,
    )
    actual_nodes = {(n['r.id'], ",".join(n['r.exposed_internet_type'])) for n in nodes}

    assert actual_nodes == expected_nodes

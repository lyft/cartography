import cartography.intel.rapid7.endpoints
from cartography.intel.azure import compute
from tests.data.azure.compute import DESCRIBE_VMS
from tests.data.rapid7.rapid7_endpoints import GET_HOSTS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


def test_load_host_data(neo4j_session, *args):
    cartography.intel.rapid7.endpoints.load_host_data(neo4j_session, GET_HOSTS, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            282,
            285,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:Rapid7Host)
        RETURN n.id
        """,
    )
    actual_nodes = {
        (
            n['n.id']
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_host_relationships(neo4j_session):
    # Create Test Azure Virtual Machines
    compute.load_vms(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_VMS,
        TEST_UPDATE_TAG,
    )

    # Create Test Rapid7 Hosts
    cartography.intel.rapid7.endpoints.load_host_data(neo4j_session, GET_HOSTS, TEST_UPDATE_TAG)

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureVirtualMachine)-[:RESOURCE]->(n2:Rapid7Host) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

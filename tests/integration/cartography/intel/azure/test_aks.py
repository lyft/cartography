from cartography.intel.azure import aks
from tests.data.azure.aks import DESCRIBE_CLUSTERS
from tests.data.azure.aks import DESCRIBE_CONTAINERGROUPS
from tests.data.azure.aks import DESCRIBE_CONTAINERREGISTRIES
from tests.data.azure.aks import DESCRIBE_CONTAINERREGISTRYREPLICATIONS
from tests.data.azure.aks import DESCRIBE_CONTAINERREGISTRYRUNS
from tests.data.azure.aks import DESCRIBE_CONTAINERREGISTRYTASKS
from tests.data.azure.aks import DESCRIBE_CONTAINERREGISTRYWEBHOOKS
from tests.data.azure.aks import DESCRIBE_CONTAINERS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


def test_load_clusters(neo4j_session):
    aks.load_aks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CLUSTERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/\
            managedClusters/TestCluster1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/\
            managedClusters/TestCluster2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCluster) RETURN r.id;
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

    aks.load_aks(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CLUSTERS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/\
            managedClusters/TestCluster1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/\
            managedClusters/TestCluster2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureCluster) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected



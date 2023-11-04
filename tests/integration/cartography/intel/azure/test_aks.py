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


def test_load_container_registries(neo4j_session):
    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerRegistry) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_registry_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureContainerRegistry) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_container_registry_replications(neo4j_session):
    aks.load_container_registry_replications(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYREPLICATIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/replications/repli1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/replications/repli2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerRegistryReplication) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_registry_replication_relationships(neo4j_session):
    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    aks.load_container_registry_replications(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYREPLICATIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/replications/repli1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/replications/repli2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureContainerRegistry)-[:CONTAIN]->(n2:AzureContainerRegistryReplication) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_container_registry_runs(neo4j_session):
    aks.load_container_registry_runs(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYRUNS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/runs/run1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/runs/run2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerRegistryRun) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_registry_run_relationships(neo4j_session):
    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    aks.load_container_registry_runs(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYRUNS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/runs/run1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/runs/run2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureContainerRegistry)-[:CONTAIN]->(n2:AzureContainerRegistryRun) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_container_registry_tasks(neo4j_session):
    aks.load_container_registry_tasks(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYTASKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/tasks/task1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/tasks/task2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerRegistryTask) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_registry_task_relationships(neo4j_session):
    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    aks.load_container_registry_tasks(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYTASKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/tasks/task1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/tasks/task2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureContainerRegistry)-[:CONTAIN]->(n2:AzureContainerRegistryTask) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_container_registry_webhooks(neo4j_session):
    aks.load_container_registry_webhooks(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYWEBHOOKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/webhooks/webhook1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/webhooks/webhook2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerRegistryWebhook) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_registry_webhook_relationships(neo4j_session):
    aks.load_container_registries(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERREGISTRIES,
        TEST_UPDATE_TAG,
    )

    aks.load_container_registry_webhooks(
        neo4j_session,
        DESCRIBE_CONTAINERREGISTRYWEBHOOKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry1/webhooks/webhook1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerRegistry/registries/TestContainerRegistry2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerRegistry/\
            registries/TestContainerRegistry2/webhooks/webhook2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureContainerRegistry)-[:CONTAIN]->(n2:AzureContainerRegistryWebhook) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_container_groups(neo4j_session):
    aks.load_container_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERGROUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainerGroup) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_group_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    aks.load_container_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERGROUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureContainerGroup) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_containers(neo4j_session):
    aks.load_containers(
        neo4j_session,
        DESCRIBE_CONTAINERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "container2",
        "container1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureContainer) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_container_relationships(neo4j_session):
    aks.load_container_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTAINERGROUPS,
        TEST_UPDATE_TAG,
    )

    aks.load_containers(
        neo4j_session,
        DESCRIBE_CONTAINERS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo2",
            "container2",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/\
            Microsoft.ContainerInstance/containerGroups/demo1",
            "container1",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureContainerGroup)-[:CONTAIN]->(n2:AzureContainer) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected

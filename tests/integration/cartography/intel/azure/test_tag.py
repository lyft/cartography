from cartography.intel.azure import tag
from tests.data.azure.tag import DESCRIBE_RESOURCE_GROUPS
from tests.data.azure.tag import DESCRIBE_TAGS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_UPDATE_TAG = 123456789


def test_load_resource_groups(neo4j_session):
    tag.load_resource_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_RESOURCE_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureResourceGroup) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_resource_group_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    tag.load_resource_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_RESOURCE_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureResourceGroup) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_tags(neo4j_session):
    tag.load_tags(
        neo4j_session,
        DESCRIBE_TAGS,
        TEST_UPDATE_TAG,
        common_job_parameters={'WORKSPACE_ID': '', 'AZURE_TENANT_ID': '', 'AZURE_SUBSCRIPTION_ID': ''}
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Resources/tags/tag1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG1/providers/Microsoft.Resources/tags/tag2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureTag) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_tags_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    tag.load_resource_groups(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_RESOURCE_GROUPS,
        TEST_UPDATE_TAG,
    )

    tag.load_tags(
        neo4j_session,
        DESCRIBE_TAGS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Resources/tags/tag1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG1/providers/Microsoft.Resources/tags/tag2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureResourceGroup)-[:TAGGED]->(n2:AzureTag) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}
    assert actual == expected

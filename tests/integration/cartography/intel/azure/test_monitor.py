from cartography.intel.azure import monitor
from tests.data.azure.monitor import DESCRIBE_LOGPROFILES

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


def test_load_log_profiles(neo4j_session):
    monitor.load_monitor_log_profiles(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_LOGPROFILES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.LogProfiles/logprofile/logprofile1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.LogProfiles/logprofile/logprofile2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureMonitorLogProfile) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_log_profiles_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    monitor.load_monitor_log_profiles(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_LOGPROFILES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.LogProfiles/logprofile/logprofile1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.LogProfiles/logprofile/logprofile2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureMonitorLogProfile) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected

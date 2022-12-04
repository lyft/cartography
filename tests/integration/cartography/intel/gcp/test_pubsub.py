import cartography.intel.gcp.pubsub
import tests.data.gcp.pubsub

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_pubsub_subscriptions(neo4j_session):
    data = tests.data.gcp.pubsub.TEST_SUBCRIPTIONS
    cartography.intel.gcp.pubsub.load_pubsub_subscriptions(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/subscriptions/sub123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPPubsubSubscription) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_pubsub_topics(neo4j_session):
    data = tests.data.gcp.pubsub.TEST_TOPICS
    cartography.intel.gcp.pubsub.load_pubsub_topics(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/topic/topic123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPPubsubTopic) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

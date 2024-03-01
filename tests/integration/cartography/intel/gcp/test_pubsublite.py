import cartography.intel.gcp.pubsublite
import tests.data.gcp.pubsublite

TEST_PROJECT_ID = 'project-123'
TEST_UPDATE_TAG = 123456789


def test_pubsublite_subscriptions(neo4j_session):
    data = tests.data.gcp.pubsublite.TEST_SUBSCRIPTIONS
    cartography.intel.gcp.pubsublite.load_pubsublite_subscriptions(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project-123/locations/us-central1/subscriptions/subscription1',
        'projects/project-123/locations/us-central1/subscriptions/subscription2',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPPubSubLiteSubscription) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_pubsublite_topics(neo4j_session):
    data = tests.data.gcp.pubsublite.TEST_TOPICS
    cartography.intel.gcp.pubsublite.load_pubsublite_topics(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project-123/locations/us-central1/topics/topic1',
        'projects/project-123/locations/us-central1/topics/topic2',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPPubSubLiteTopic) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_pubsublite_subcription_to_topic_relation(neo4j_session):
    data = tests.data.gcp.pubsublite.TEST_TOPICS
    cartography.intel.gcp.pubsublite.load_pubsublite_topics(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )
    data = tests.data.gcp.pubsublite.TEST_SUBSCRIPTIONS
    cartography.intel.gcp.pubsublite.load_pubsublite_subscriptions(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            'projects/project-123/locations/us-central1/subscriptions/subscription1',
            'projects/project-123/locations/us-central1/topics/topic1',
        ),
        (
            'projects/project-123/locations/us-central1/subscriptions/subscription2',
            'projects/project-123/locations/us-central1/topics/topic2',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (m:GCPPubSubLiteSubscription)<-[:HAS]-(n:GCPPubSubLiteTopic) RETURN m.id,n.id;
        """,
    )

    actual_nodes = {(n['m.id'], n['n.id']) for n in nodes}

    assert actual_nodes == expected_nodes

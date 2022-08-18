import cartography.intel.gcp.cloud_logging
import tests.data.gcp.cloud_logging

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_logging_metrics(neo4j_session):
    data = tests.data.gcp.cloud_logging.TEST_METRICS
    cartography.intel.gcp.cloud_logging.load_logging_metrics(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/metrics/metric123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPLoggingMetric) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_logging_sinks(neo4j_session):
    data = tests.data.gcp.cloud_logging.TEST_SINKS
    cartography.intel.gcp.cloud_logging.load_logging_sinks(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/sinks/sink123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPLoggingSink) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes
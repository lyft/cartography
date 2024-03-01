import cartography.intel.aws.cloudwatch
from tests.data.aws.cloudwatch import DESCRIBE_EVENT_RULES_RESPONSE
from tests.data.aws.cloudwatch import DESCRIBE_EVENTBUS_RESPONSE
from tests.data.aws.cloudwatch import DESCRIBE_LOG_GROUPS_RESPONSE
from tests.data.aws.cloudwatch import DESCRIBE_METRICS_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_cloudwatch_event_bus_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudwatch_event_bus_data(neo4j_session)
    expected_nodes = {
        "arn:aws:cloudwatch:us-east-1:123456789012:eventbus/466df9e0-0dff-08e3-8e2f-5088487c4896",
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSEventBridgeEventBus) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudwatch_event_bus_data(neo4j_session):
    cartography.intel.aws.cloudwatch.load_event_buses(
        neo4j_session,
        DESCRIBE_EVENTBUS_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )


def test_load_cloudwatch_log_groups_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudwatch_log_groups_data(neo4j_session)
    expected_nodes = {
        "arn:aws:logs:us-west-2:0123456789012:log-group:my-logs:*",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudWatchLogGroup) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudwatch_log_groups_data(neo4j_session):
    cartography.intel.aws.cloudwatch.load_log_groups(
        neo4j_session,
        DESCRIBE_LOG_GROUPS_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )


def test_load_cloudwatch_metrics_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudwatch_metrics_data(neo4j_session)
    expected_nodes = {
        "PublishSize",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudWatchMetric) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudwatch_metrics_data(neo4j_session):
    cartography.intel.aws.cloudwatch.load_metrics(
        neo4j_session,
        DESCRIBE_METRICS_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )


def test_load_cloudwatch_event_rules_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudwatch_event_rules_data(neo4j_session)
    expected_nodes = {
        "arn:aws:events:us-east-1:123456789012:rule/test",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSEventBridgeRule) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudwatch_event_rules_data(neo4j_session):
    cartography.intel.aws.cloudwatch.load_event_rules(
        neo4j_session,
        DESCRIBE_EVENT_RULES_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )

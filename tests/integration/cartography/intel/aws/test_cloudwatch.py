import copy

import cartography.intel.aws.cloudwatch
import tests.data.aws.cloudwatch

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_cloudwatch_log_group_transform_and_load(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudwatch.CLOUD_WATCH_LOG_GROUPS)
    log_groups = cartography.intel.aws.cloudwatch.transform_cloudwatch_log_groups(data)
    cartography.intel.aws.cloudwatch.load_cloudwatch_log_groups(
        neo4j_session,
        log_groups,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:logs:us-east-1:000000000000:log-group:logGroupName1:*",
        "arn:aws:logs:us-east-1:000000000000:log-group:logGroupName2:*",
    }
    nodes = neo4j_session.run(
        """
        MATCH (lg:CloudWatchLogGroup) RETURN lg.id as id;
        """,
    )
    actual_nodes = {n['id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_cloudwatch_alarm_transform_and_load(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudwatch.CLOUD_WATCH_ALARMS)
    cartography.intel.aws.cloudwatch.load_cloudwatch_alarms(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "alarmArn1",
        "alarmArn2",
    }
    nodes = neo4j_session.run(
        """
        MATCH (cwa:CloudWatchAlarm) RETURN cwa.id as id;
        """,
    )
    actual_nodes = {n['id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_cloudwatch_transform_and_load(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudwatch.CLOUD_WATCH_LOG_GROUPS)
    log_groups = cartography.intel.aws.cloudwatch.transform_cloudwatch_log_groups(data)
    cartography.intel.aws.cloudwatch.load_cloudwatch_log_groups(
        neo4j_session,
        log_groups,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = copy.deepcopy(tests.data.aws.cloudwatch.CLOUD_WATCH_METRIC_FILTERS)
    metric_filters = cartography.intel.aws.cloudwatch.transform_cloudwatch_metric_filters(
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )
    cartography.intel.aws.cloudwatch.load_cloudwatch_metric_filters(
        neo4j_session,
        metric_filters,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = copy.deepcopy(tests.data.aws.cloudwatch.CLOUD_WATCH_ALARMS)
    cartography.intel.aws.cloudwatch.load_cloudwatch_alarms(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:logs:us-east-1:000000000000:log-group:logGroupName1:*",
            "arn:aws:logs:us-east-1:000000000000:metric_filter:filterName1",
            "alarmArn1",
        ),
        (
            "arn:aws:logs:us-east-1:000000000000:log-group:logGroupName2:*",
            "arn:aws:logs:us-east-1:000000000000:metric_filter:filterName2",
            "alarmArn2",
        ),
    }
    nodes = neo4j_session.run(
        """
        MATCH (lg:CloudWatchLogGroup)-[:HAS_METRIC_FILTER]->(mf:CloudWatchMetricFilter)
        OPTIONAL MATCH (a:CloudWatchAlarm)
        WHERE a.metric_name IS NOT NULL
        AND a.metric_name = mf.metric_transformation_name
        RETURN lg.id as lg_id, mf.id as mf_id, a.id as a_id;
        """,
    )
    actual_nodes = {(n['lg_id'], n['mf_id'], n['a_id']) for n in nodes}
    assert actual_nodes == expected_nodes

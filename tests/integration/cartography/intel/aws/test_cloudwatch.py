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
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "logGroupName1Arn",
        "logGroupName2Arn",
    }
    nodes = neo4j_session.run(
        """
        MATCH (lg:CloudWatchLogGroup) RETURN lg.id as id;
        """,
    )
    actual_nodes = {n['id'] for n in nodes}
    assert actual_nodes == expected_nodes



import copy

import cartography.intel.aws.cloudtrail
import tests.data.aws.cloudtrail

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_cloudtrail_trails(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUDTRAIL_TRAILS)
    trails, _, _ = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)
    cartography.intel.aws.cloudtrail.load_cloudtrail_trails(
        neo4j_session,
        trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "TrailARN1",
        "TrailARN2",
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail) RETURN t.arn as arn;
        """,
    )
    actual_nodes = {n['arn'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_transform_and_load_trail_and_related_objects(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUDTRAIL_TRAILS)
    trails, s3_buckets, log_groups = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)
    cartography.intel.aws.cloudtrail.load_cloudtrail_s3_buckets(
        neo4j_session,
        s3_buckets,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_log_groups(
        neo4j_session,
        log_groups,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_trails(
        neo4j_session,
        trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("TrailARN1", "S3BucketName", "CloudWatchLogsLogGroupArn", None),
        ("TrailARN2", "S3BucketName", "CloudWatchLogsLogGroupArn", 1634041146),
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail)-[:DELIVERS_TO]->(s:S3Bucket), (t)-[:DELIVERS_TO]->(lg:CloudWatchLogGroup)
        RETURN
            t.id as id,
            s.name as bucketName,
            lg.id as lg_id,
            t.latest_cloud_watch_logs_delivery_time as cloudwatch_time;
        """,
    )
    actual_nodes = {(n['id'], n['bucketName'], n['lg_id'], n['cloudwatch_time']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_transform_and_load_trail_and_event_selectors(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUDTRAIL_TRAILS)
    trails, _, _ = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)

    data = copy.deepcopy(tests.data.aws.cloudtrail.TRAIL_ARN_TO_CLOUDTRAIL_EVENT_SELECTORS)
    transformed_event_selectors = []
    for trail in trails:
        event_selectors = cartography.intel.aws.cloudtrail.transform_event_selectors(data[trail['TrailARN']], trail)
        transformed_event_selectors.extend(event_selectors)

    cartography.intel.aws.cloudtrail.load_cloudtrail_trails(
        neo4j_session,
        trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_event_selectors(
        neo4j_session,
        transformed_event_selectors,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("TrailARN1", "All", True, '338d275a120a98d2c15efcac75ca60bfd7b7991d953be813b5d7632735a1a6bd'),
        ("TrailARN1", "WriteOnly", False, 'd553c54a99d2efdab311e690b924ad01cc20213462e39ee68997584dfdca56d6'),
        ("TrailARN2", "All", True, 'da1b0f3420bae794215dcbd831015305ec39ff57a705bf6dd61a8414a6cea45c'),
    }
    nodes = neo4j_session.run(
        """
        MATCH (es:CloudTrailEventSelector)-[:APPLIES_TO]->(t:CloudTrail)
        RETURN
            t.id as t_id,
            es.read_write_type as read_write_type,
            es.include_management_events as include_management_events,
            es.id as es_id;
        """,
    )
    actual_nodes = {(n['t_id'], n['read_write_type'], n['include_management_events'], n['es_id']) for n in nodes}
    assert actual_nodes == expected_nodes

import copy
import itertools

import cartography.intel.aws.cloudtrail
import tests.data.aws.cloudtrail
import tests.integration.cartography.intel.aws.common

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_cloudtrail_trails(neo4j_session):
    tests.integration.cartography.intel.aws.common.create_test_account(
        neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )

    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUDTRAIL_TRAILS)
    native_trails, foreign_trails, _, _ = \
        cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(
            data, TEST_ACCOUNT_ID,
        )
    cartography.intel.aws.cloudtrail.load_cloudtrail_native_trails(
        neo4j_session,
        native_trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_foreign_trails(
        neo4j_session,
        foreign_trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1", '000000000000', '000000000000'),
        ("arn:aws:cloudtrail:us-east-1:000000000001:trail/TRAIL2", '000000000000', None),
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail)-[:MONITORS]->(a1:AWSAccount)
        OPTIONAL MATCH (t)<-[:RESOURCE]-(a2:AWSAccount)
        RETURN t.arn as arn, a1.id, a2.id;
        """,
    )
    actual_nodes = {(n['arn'], n['a1.id'], n['a2.id']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_transform_and_load_trail_and_related_objects(neo4j_session):
    tests.integration.cartography.intel.aws.common.create_test_account(
        neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )

    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUDTRAIL_TRAILS)
    native_trails, foreign_trails, s3_buckets, log_groups = \
        cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(
            data, TEST_ACCOUNT_ID,
        )
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
    cartography.intel.aws.cloudtrail.load_cloudtrail_native_trails(
        neo4j_session,
        native_trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_foreign_trails(
        neo4j_session,
        foreign_trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1",
            "S3BucketName", "CloudWatchLogsLogGroupArn", None,
        ),
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
    native_trails, foreign_trails, s3_buckets, log_groups = \
        cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(
            data, TEST_ACCOUNT_ID,
        )
    data = copy.deepcopy(tests.data.aws.cloudtrail.TRAIL_ARN_TO_CLOUDTRAIL_EVENT_SELECTORS)
    transformed_event_selectors = []
    for trail in itertools.chain(native_trails, foreign_trails):
        event_selectors = cartography.intel.aws.cloudtrail.transform_event_selectors(data[trail['TrailARN']], trail)
        transformed_event_selectors.extend(event_selectors)

    cartography.intel.aws.cloudtrail.load_cloudtrail_native_trails(
        neo4j_session,
        native_trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_foreign_trails(
        neo4j_session,
        foreign_trails,
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
        (
            "arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1",
            "All", True, '522b83817ed2ccca5e1d63ad74b8650ac6168762f442e1b0287c8df99ff0443d',
        ),
        (
            "arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1",
            "WriteOnly", False, 'd5db886afb74285387687da44e7ba19c7761e1b7037bbc47d2c74b4cddee4023',
        ),
        (
            "arn:aws:cloudtrail:us-east-1:000000000001:trail/TRAIL2",
            "All", True, '5a251f316e217fd06b4983e5b18bd9218e439302c021aae1f3479b25e4ce11fc',
        ),
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

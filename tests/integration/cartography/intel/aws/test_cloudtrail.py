import copy

import cartography.intel.aws.cloudtrail
import tests.data.aws.cloudtrail

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_cloudtrail_trails(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUD_TRAILS)
    print(data)
    trails, _ = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)
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


def test_transform_and_load(neo4j_session):
    data = copy.deepcopy(tests.data.aws.cloudtrail.CLOUD_TRAILS)
    trails, s3_buckets = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)
    cartography.intel.aws.cloudtrail.load_cloudtrail_s3_buckets(
        neo4j_session,
        s3_buckets,
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
        ("TrailARN1", "S3BucketName", None),
        ("TrailARN2", "S3BucketName", 1634041146),
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail)-[:DELIVERS_TO]->(s:S3Bucket)
        RETURN t.id as id, s.name as bucketName, t.latest_cloud_watch_logs_delivery_time as cloudwatch_time;
        """,
    )
    actual_nodes = {(n['id'], n['bucketName'], n['cloudwatch_time']) for n in nodes}
    assert actual_nodes == expected_nodes

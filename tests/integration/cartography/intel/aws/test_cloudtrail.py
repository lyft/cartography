import cartography.intel.aws.cloudtrail
import tests.data.aws.cloudtrail

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789

def test_load_cloudtrail_trails(neo4j_session):
    data = tests.data.aws.cloudtrail.CLOUD_TRAILS
    cartography.intel.aws.cloudtrail.load_cloudtrail_trails(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "TrailARN1",
        "TrailARN2"
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail) RETURN t.arn as arn;
        """,
    )
    actual_nodes = {n['arn'] for n in nodes}
    assert actual_nodes == expected_nodes

def test_transform_and_load(neo4j_session):
    data = tests.data.aws.cloudtrail.CLOUD_TRAILS
    trails, s3_buckets = cartography.intel.aws.cloudtrail.transform_trail_and_related_objects(data)
    cartography.intel.aws.cloudtrail.load_cloudtrail_s3_buckets(
        neo4j_session,
        s3_buckets,
        TEST_UPDATE_TAG
    )
    cartography.intel.aws.cloudtrail.load_cloudtrail_trails(
        neo4j_session,
        trails,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        ("TrailARN1", "S3BucketName"),
        ("TrailARN2", "S3BucketName")
    }
    nodes = neo4j_session.run(
        """
        MATCH (t:CloudTrail)-[:DELIVERS_TO]->(s:S3Bucket)
        RETURN t.arn as arn, s.name as bucketName;
        """,
    )
    actual_nodes = {(n['arn'], n['bucketName']) for n in nodes}
    assert actual_nodes == expected_nodes

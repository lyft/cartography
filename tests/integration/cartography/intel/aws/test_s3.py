import cartography.intel.aws.s3
import tests.data.aws.s3


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_s3_buckets(neo4j_session, *args):
    """
    Ensure that expected buckets get loaded with their key fields.
    """
    data = tests.data.aws.s3.LIST_BUCKETS
    cartography.intel.aws.s3.load_s3_buckets(neo4j_session, data, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            "bucket-1",
            "bucket-1",
            "eu-west-1",
        ),
        (
            "bucket-2",
            "bucket-2",
            "me-south-1",
        ),
        (
            "bucket-3",
            "bucket-3",
            None,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket) return s.id, s.name, s.region
        """,
    )
    actual_nodes = {
        (
            n['s.id'],
            n['s.name'],
            n['s.region'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_s3_encryption(neo4j_session, *args):
    """
    Ensure that expected bucket gets loaded with their encryption fields.
    """
    data = tests.data.aws.s3.GET_ENCRYPTION
    cartography.intel.aws.s3._load_s3_encryption(neo4j_session, data, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            "bucket-1",
            True,
            "aws:kms",
            "arn:aws:kms:eu-east-1:000000000000:key/9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
            False,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:S3Bucket)
        WHERE s.id = 'bucket-1'
        RETURN s.id, s.default_encryption, s.encryption_algorithm, s.encryption_key_id, s.bucket_key_enabled
        """,
    )
    actual_nodes = {
        (
            n['s.id'],
            n['s.default_encryption'],
            n['s.encryption_algorithm'],
            n['s.encryption_key_id'],
            n['s.bucket_key_enabled'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

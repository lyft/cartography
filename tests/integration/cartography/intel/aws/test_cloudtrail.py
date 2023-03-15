from cartography.intel.aws.cloudtrail import load_trails
from tests.data.aws.cloudtrail import DESCRIBE_TRAILS
from tests.data.aws.s3 import LIST_BUCKETS, LIST_STATEMENTS
from cartography.intel.aws.s3 import load_s3_buckets, _load_s3_policies, parse_policy
from cartography.util import run_analysis_job

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '12345'


def test_load_cloudtrails(neo4j_session):
    neo4j_session.run(
        """
            MERGE (aws:AWSAccount{id: $aws_account_id})<-[:OWNER]-(:CloudanixWorkspace{id: $workspace_id})
            ON CREATE SET aws.firstseen = timestamp()
            SET aws.lastupdated = $aws_update_tag
            """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
        workspace_id=TEST_WORKSPACE_ID
    )
    load_trails(neo4j_session, DESCRIBE_TRAILS, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudTrailTrail) return n.id
        """
    )

    actual_nodes = {n["n.id"] for n in nodes}

    expected_nodes = {'trail1_arn', 'trail2_arn'}

    assert expected_nodes == actual_nodes


def test_cloudtrails_analysis(neo4j_session):
    load_s3_buckets(neo4j_session, LIST_BUCKETS, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    policy = parse_policy('bucket-1', LIST_STATEMENTS)
    _load_s3_policies(neo4j_session, [policy], TEST_UPDATE_TAG)
    load_trails(neo4j_session, DESCRIBE_TRAILS, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    nodes = neo4j_session.run(
        """
        MATCH (s3:S3Bucket)<-[:HAS_BUCKET]-(n:AWSCloudTrailTrail) return s3.id, n.id
        """
    )

    actual_nodes = {(n["n.id"], n["s3.id"]) for n in nodes}

    expected_nodes = {('trail1_arn', 'bucket-1'), ('trail2_arn', 'bucket-2')}

    assert expected_nodes == actual_nodes

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    run_analysis_job('aws_cloudtrail_asset_exposure.json', neo4j_session, common_job_parameters)

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudTrailTrail{anonymous_access: true}) RETURN n.id
        """
    )

    actual_nodes = {n["n.id"] for n in nodes}

    expected_nodes = {'trail1_arn'}

    assert expected_nodes == actual_nodes

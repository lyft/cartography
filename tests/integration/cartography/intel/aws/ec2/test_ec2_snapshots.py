import cartography.intel.aws.ec2.snapshots
import tests.data.aws.ec2.snapshots

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_volumes(neo4j_session):
    data = tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS
    cartography.intel.aws.ec2.snapshots.load_snapshots(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "sn-01", "sn-02",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EBSSnapshot) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_volumes_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: {aws_account_id}})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = {aws_update_tag}
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test Volumes
    data = tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS
    cartography.intel.aws.ec2.snapshots.load_snapshots(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_ACCOUNT_ID, 'sn-01'),
        (TEST_ACCOUNT_ID, 'sn-02'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EBSSnapshot) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

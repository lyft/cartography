import cartography.intel.aws.emr
import tests.data.aws.emr

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_emr_clusters_nodes(neo4j_session):
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_arns = {
        "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",
        "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EMRCluster) RETURN r.arn, r.firstseen;
        """,
    )
    actual_data = {(n['r.arn'], n['r.firstseen']) for n in nodes}

    for arn, firstseen in actual_data:
        assert arn in expected_arns
        assert firstseen is not None  # Issue #1064


def test_load_emr_clusters_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test EMR Clusters
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (TEST_ACCOUNT_ID, 'arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome'),
        (TEST_ACCOUNT_ID, 'arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EMRCluster) RETURN n1.id, n2.arn;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.arn']) for r in result
    }

    assert actual == expected

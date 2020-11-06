import cartography.intel.aws.eks
import tests.data.aws.eks

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_eks_clusters_nodes(neo4j_session):
    data = tests.data.aws.eks.DESCRIBE_CLUSTERS
    cartography.intel.aws.eks.load_eks_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
        "arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EKSCluster) RETURN r.arn;
        """,
    )
    actual_nodes = {n['r.arn'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_eks_clusters_relationships(neo4j_session):
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

    # Load Test EKS Clusters
    data = tests.data.aws.eks.DESCRIBE_CLUSTERS
    cartography.intel.aws.eks.load_eks_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (TEST_ACCOUNT_ID, 'arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1'),
        (TEST_ACCOUNT_ID, 'arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EKSCluster) RETURN n1.id, n2.arn;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.arn']) for r in result
    }

    assert actual == expected

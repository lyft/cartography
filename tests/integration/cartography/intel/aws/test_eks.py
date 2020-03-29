import cartography.intel.aws.eks
import tests.data.aws.eks

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_eks_clusters(neo4j_session):
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
        """
    )
    actual_nodes = {n['r.arn'] for n in nodes}
    assert actual_nodes == expected_nodes

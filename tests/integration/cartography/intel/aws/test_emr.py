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

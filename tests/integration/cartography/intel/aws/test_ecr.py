import cartography.intel.aws.ecr
import tests.data.aws.ecr

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_ecr_repositories(neo4j_session):
    data = tests.data.aws.ecr.DESCRIBE_REPOSITORIES

    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ECRRepository) RETURN r.arn;
        """
    )
    actual_nodes = {(n['r.arn'] for n in nodes)}
    assert actual_nodes == expected_nodes


def test_load_ecr_images(neo4j_session):
    pass

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
    repo_data = tests.data.aws.ecr.DESCRIBE_REPOSITORIES

    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES

    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = set()

    nodes = neo4j_session.run(
        """
        MATCH (repo:ECRRepository)-[:IMAGE]->(image:ECRImage) RETURN repo.arn, image.digest;
        """
    )
    actual_nodes = {(n['repo.arn'], n['image.digest'] for n in nodes)}
    assert actual_nodes == expected_nodes

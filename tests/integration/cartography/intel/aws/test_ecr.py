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
    actual_nodes = {n['r.arn'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_ecr_repository_images(neo4j_session):
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
        data,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    # TODO it's possible to have the same image in multiple repositories -- current code doesn't represent that in the
    #      graph well
    expected_nodes = {
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            '1',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000001',
            '2',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/sample-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            '1',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/sample-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000011',
            '2',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/test-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            '1234567890',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/test-repository',
            'sha256:0000000000000000000000000000000000000000000000000000000000000021',
            '1',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo:ECRRepository)-[:IMAGE]->(image:ECRImage) RETURN repo.arn, image.digest, image.tag;
        """
    )
    actual_nodes = {(n['repo.arn'], n['image.digest'], n['image.tag']) for n in nodes}
    assert actual_nodes == expected_nodes
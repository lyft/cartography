import cartography.intel.aws.ecr
import tests.data.aws.ecr

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session):
    repo_data = tests.data.aws.ecr.DESCRIBE_REPOSITORIES
    cartography.intel.aws.ecr.load_ecr_repositories(
        neo4j_session,
        repo_data['repositories'],
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_ecr_repositories(neo4j_session):
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    expected_nodes = {
        "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
        "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:ECRRepository) RETURN r.arn;
        """,
    )
    actual_nodes = {n['r.arn'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_ecr_repository_images(neo4j_session):
    """
    Ensure the connection (:ECRRepository)-[:REPO_IMAGE]->(:ECRRepositoryImage) exists.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list = cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo ARN, image tag)
    expected_nodes = {
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            '1',
        ),
        (
            'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            '2',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo:ECRRepository{id:"arn:aws:ecr:us-east-1:000000000000:repository/example-repository"})
        -[:REPO_IMAGE]->(image:ECRRepositoryImage)
        RETURN repo.arn, image.tag;
        """,
    )
    actual_nodes = {(n['repo.arn'], n['image.tag']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_ecr_images(neo4j_session):
    """
    Ensure the connection (:ECRRepositoryImage)-[:IMAGE]->(:ECRImage) exists.
    A single ECRImage may be referenced by many ECRRepositoryImages.
    """
    _ensure_local_neo4j_has_test_ecr_repo_data(neo4j_session)

    data = tests.data.aws.ecr.LIST_REPOSITORY_IMAGES
    repo_images_list = cartography.intel.aws.ecr.transform_ecr_repository_images(data)
    cartography.intel.aws.ecr.load_ecr_repository_images(
        neo4j_session,
        repo_images_list,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )

    # Tuples of form (repo image ARN, image SHA)
    expected_nodes = {
        (
            "000000000000.dkr.ecr.us-east-1/test-repository:1234567890",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1/sample-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "000000000000.dkr.ecr.us-east-1/example-repository:1",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (repo_image:ECRRepositoryImage)-[:IMAGE]->
        (image:ECRImage{digest:"sha256:0000000000000000000000000000000000000000000000000000000000000000"})
        RETURN repo_image.id, image.digest;
        """,
    )
    actual_nodes = {(n['repo_image.id'], n['image.digest']) for n in nodes}
    assert actual_nodes == expected_nodes

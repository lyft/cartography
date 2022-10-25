import cartography.intel.aws.cloudfront
import tests.data.aws.cloudfront

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_repository_associations(neo4j_session):
    data = tests.data.aws.cloudfront.GET_LIST_DISTRIBUTION
    cartography.intel.aws.cloudfront.load_cloudfront_distributions(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:cloudfront::123456789:distribution/test1",
        "arn:aws:cloudfront::123456789:distribution/test2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:CloudFrontDistribution) RETURN r.arn;
        """,
    )
    actual_nodes = {n['r.arn'] for n in nodes}

    assert actual_nodes == expected_nodes

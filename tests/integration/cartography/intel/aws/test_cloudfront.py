import cartography.intel.aws.cloudfront
from tests.data.aws.cloudfront import DESCRIBE_DISTRIBUTION_RESPONSE


TEST_UPDATE_TAG = 123456789


def test_load_cloudfront_distributions_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudfront_distributions_data(neo4j_session)
    expected_nodes = {
        "arn:aws:cloudfront::123456789012:distribution/EDFDVBD632BHDS5",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudfrontDistribution) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudfront_distributions_data(neo4j_session):
    cartography.intel.aws.cloudfront.load_cloudfront_distributions(
        neo4j_session,
        DESCRIBE_DISTRIBUTION_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )

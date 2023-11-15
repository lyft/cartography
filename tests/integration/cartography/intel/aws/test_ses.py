import cartography.intel.aws.ses
from tests.data.aws.ses import DESCRIBE_IDENTITIES_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_ses_identitye_data(neo4j_session):
    _ensure_local_neo4j_has_test_ses_identity_data(neo4j_session)
    expected_nodes = {
        "arn:aws:ses:us-east-1:123456789012:identity/example.com",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSSESIdentity) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_ses_identity_data(neo4j_session):
    cartography.intel.aws.ses.load_ses_identity(
        neo4j_session,
        DESCRIBE_IDENTITIES_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )

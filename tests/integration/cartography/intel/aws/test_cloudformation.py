import cartography.intel.aws.cloudformation
from tests.data.aws.cloudformation import DESCRIBE_STACKS_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_cloudformation_stack_data(neo4j_session):
    _ensure_local_neo4j_has_test_cloudformation_stack_data(neo4j_session)
    expected_nodes = {
        "arn:aws:cloudformation:us-east-1:123456789012:stack/myteststack/466df9e0-0dff-08e3-8e2f-5088487c4896",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSCloudformationStack) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_cloudformation_stack_data(neo4j_session):
    cartography.intel.aws.cloudformation.load_cloudformation_stack(
        neo4j_session,
        DESCRIBE_STACKS_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )

import cartography.intel.aws.elasticsearch
from tests.data.aws.elasticsearch import DESCRIBE_INSTANCE_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_es_reserved_instance_data(neo4j_session):
    _ensure_local_neo4j_has_test_es_reserved_instance_data(neo4j_session)
    expected_nodes = {
        "arn:aws:es:us-east-1:123456789:reserved-instances/my-reservation",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AWSESReservedInstance) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_es_reserved_instance_data(neo4j_session):
    cartography.intel.aws.elasticsearch.load_elasticsearch_reserved_instances(
        neo4j_session,
        DESCRIBE_INSTANCE_RESPONSE,
        '123456789012',
        TEST_UPDATE_TAG,
    )

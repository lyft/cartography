import cartography.intel.aws.rds
from tests.data.aws.rds import DESCRIBE_DBINSTANCES_RESPONSE
TEST_UPDATE_TAG = 123456789


def test_load_rds_instances_basic(neo4j_session):
    """Test that we successfully load RDS instance nodes to the graph"""
    cartography.intel.aws.rds.load_rds_instances(
        neo4j_session,
        DESCRIBE_DBINSTANCES_RESPONSE['DBInstances'],
        'us-east1',
        '1234',
        TEST_UPDATE_TAG,
    )
    query = """MATCH(rds:RDSInstance) RETURN rds.id, rds.arn, rds.storage_encrypted"""
    nodes = neo4j_session.run(query)

    actual_nodes = {(n['rds.id'], n['rds.arn'], n['rds.storage_encrypted']) for n in nodes}
    expected_nodes = {
        (
            'arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0',
            'arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0',
            True,
        ),
    }
    assert actual_nodes == expected_nodes

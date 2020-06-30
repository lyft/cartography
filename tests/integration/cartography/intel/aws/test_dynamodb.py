import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_dynamodb(neo4j_session):
    data = tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES['Tables']

    cartography.intel.aws.dynamodb.load_dynamodb_tables(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_rows = 1000000
    expected_nodes = {
        ("arn:aws:dynamodb:us-east-1:000000000000:table/example-table", expected_rows),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/sample-table", expected_rows),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/model-table", expected_rows),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/basic-table", expected_rows),
    }

    nodes = neo4j_session.run(
        """
        MATCH (d:DynamoDBTable) return d.arn, d.rows
        """,
    )
    actual_nodes = {(n['d.arn'], n['d.rows']) for n in nodes}
    assert actual_nodes == expected_nodes

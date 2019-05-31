import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_dynamodb(neo4j_session):
    data = tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES_FORMATTED

    cartography.intel.aws.dynamodb.load_dynamodb_tables(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )


def test_transform_dynamodb(neo4j_session):
    data = {"Tables": []}
    for table in tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"]:
        data["Tables"].append(cartography.intel.aws.dynamodb.transform_dynamo_db_tables(table))

    cartography.intel.aws.dynamodb.load_dynamodb_tables(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )

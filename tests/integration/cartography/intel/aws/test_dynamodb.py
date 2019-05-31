import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_dynamodb(neo4j_session):
    data = tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES

    cartography.intel.aws.dynamodb.load_dynamodb_tables(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )


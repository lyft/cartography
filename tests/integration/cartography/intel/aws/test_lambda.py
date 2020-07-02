import cartography.intel.aws.lambda_function
import tests.data.aws.lambda_function

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-west-2'
TEST_UPDATE_TAG = 123456789


def test_load_lambda_functions(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

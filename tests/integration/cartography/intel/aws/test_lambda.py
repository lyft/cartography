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

    expected_nodes = {
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AWSLambda) RETURN r.arn;
        """,
    )

    actual_nodes = {n['r.arn'] for n in nodes}

    assert actual_nodes == expected_nodes

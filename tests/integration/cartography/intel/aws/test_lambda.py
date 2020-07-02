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


# def test_load_lambda_function_creates_relationships(neo4j_session):
#     data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

#     cartography.intel.aws.lambda_function.load_lambda_functions(
#         neo4j_session,
#         data,
#         TEST_REGION,
#         TEST_ACCOUNT_ID,
#         TEST_UPDATE_TAG,
#     )
    
#     result = neo4j_session.run(
#         """
#         MATCH (n1:AWSLambda)-[:STS_ASSUME_ROLE_ALLOW]->(n2:AWSPrincipal) RETURN n1.arn, n2.arn;
#         """,
#     )
    
#     expected_nodes = {
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-1", "arn:aws:iam::000000000000:role/sample-role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-2", "arn:aws:iam::000000000000:role/service-role/sample-role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-3", "arn:aws:iam::000000000000:role/Lambda-Testing-Role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-4", "arn:aws:iam::000000000000:role/sample-role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-5", "arn:aws:iam::000000000000:role/Lambda-Testing-Role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-6", "arn:aws:iam::000000000000:role/sample-role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-7", "arn:aws:iam::000000000000:role/sample-role-2"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-8", "arn:aws:iam::000000000000:role/sample-role"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-9", "arn:aws:iam::000000000000:role/sample-role-3"),
#         ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-10", "arn:aws:iam::000000000000:role/sample-role-4"),        
#     }

#     actual_nodes = {
#         (r['n1.arn'], r['n2.arn']) for r in result
#     }
#     assert actual_nodes == expected_nodes

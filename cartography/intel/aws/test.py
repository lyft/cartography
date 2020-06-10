import boto3

client = boto3.client('lambda')

paginator = client.get_paginator('list_functions')
lambda_functions = []
for page in paginator.paginate():
    for each_function in page['Functions']:
        lambda_functions.append(each_function)
print ({'AWSLambda': lambda_functions})
# print(lambda_functions)
# print(len(lambda_functions))
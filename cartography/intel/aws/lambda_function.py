import logging

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_lambda_data(boto3_session, region):
    """
    Create an Lambda boto3 client and grab all the lambda functions.
    """
    client = boto3_session.client('lambda', region_name=region)
    paginator = client.get_paginator('list_functions')
    lambda_functions = []
    for page in paginator.paginate():
        for each_function in page['Functions']:
            lambda_functions.append(each_function)
    return lambda_functions


@timeit
def load_lambda_functions(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_lambda_functions = """
    MERGE (lambda:AWSLambda{id: {Arn}})
    ON CREATE SET lambda.firstseen = timestamp()
    SET lambda.name = {LambdaName},
    lambda.modifieddate = {LastModified},
    lambda.arn = {Arn},
    lambda.runtime = {Runtime},
    lambda.description = {Description},
    lambda.timeout = {Timeout},
    lambda.memory = {MemorySize},
    lambda.lastupdated = {aws_update_tag}
    WITH lambda
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(lambda)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH lambda
    MATCH (role:AWSPrincipal{arn: {Role}})
    MERGE (lambda)-[r:STS_ASSUME_ROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for lambda_function in data:
        neo4j_session.run(
            ingest_lambda_functions,
            LambdaName=lambda_function["FunctionName"],
            Arn=lambda_function["FunctionArn"],
            Runtime=lambda_function["Runtime"],
            Role=lambda_function["Role"],
            Description=lambda_function["Description"],
            Timeout=lambda_function["Timeout"],
            MemorySize=lambda_function["MemorySize"],
            LastModified=lambda_function["LastModified"],
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_lambda(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_lambda_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_lambda_functions(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.info("Syncing Lambda for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_lambda_data(boto3_session, region)
        load_lambda_functions(neo4j_session, data, region, current_aws_account_id, aws_update_tag)

    cleanup_lambda(neo4j_session, common_job_parameters)


def sync(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    sync_lambda_functions(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
    )

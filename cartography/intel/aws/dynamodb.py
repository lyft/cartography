import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_dynamodb_tables(session, region):
    client = session.client('dynamodb', region_name=region)
    paginator = client.get_paginator('list_tables')
    dynamodb_tables = []
    for page in paginator.paginate():
        dynamodb_tables.extend(page['TableNames'])
    return {'TableNames': dynamodb_tables}


def load_dynamodb_tables(session, data, region, current_aws_account_id, aws_update_tag):
    ingest_table = """
    MERGE (table:DynamoDBTable{id: {Arn}})
    ON CREATE SET table.firstseen = timestamp(), table.arn = {Arn}, table.name = {TableName},
    table.region = {Region}
    SET table.lastupdated = {aws_update_tag}
    WITH table
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(table)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for table_name in data["TableNames"]:
        arn = "arn:aws:dynamodb:{0}:{1}:table/{2}".format(region, current_aws_account_id, table_name)
        session.run(
            ingest_table,
            Arn=arn,
            TableName=table_name,
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag
        )


def cleanup_dynamodb_tables(session, common_job_parameters):
    run_cleanup_job('aws_import_dynamodb_tables_cleanup.json', session, common_job_parameters)


def sync_dynamodb_tables(session, boto3_session, regions, current_aws_account_id, aws_update_tag,
                         common_job_parameters):
    for region in regions:
        logger.info("Syncing DynamoDB for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_dynamodb_tables(boto3_session, region)
        load_dynamodb_tables(session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_dynamodb_tables(session, common_job_parameters)

import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_dynamodb_tables(session, region):
    client = session.client('dynamodb', region_name=region)
    paginator = client.get_paginator('list_tables')
    dynamodb_tables = []
    for page in paginator.paginate():
        for table in (client.describe_table(item) for item in page):
            table_properties = {
                "TableName": table['Table']['TableNames'],
                "Rows": table['Table']['ItemCount'],
                "GSIs": [],
                "Size": table['Table']['TableSizeBytes'],
                "ProvisionedThroughputReadCapacityUnits": table['Table']['ProvisionedThroughput']['ReadCapacityUnits'],
                "ProvisionedThroughputWriteCapacityUnits": table['Table']['ProvisionedThroughput']['WriteCapacityUnits']
            }
            for gsi in table['Table']['GlobalSecondaryIndexes']:
                table_properties['GSIs'].append({
                    "Arn": gsi['IndexArn'],
                    "GSIName": gsi['IndexName'],
                    "ProvisionedThroughputReadCapacityUnits": gsi['ProvisionedThroughput']['ReadCapacityUnits'],
                    "ProvisionedThroughputWriteCapacityUnits": gsi['ProvisionedThroughput']['WriteCapacityUnits'],
                })
            dynamodb_tables.append(table_properties)
    return {'Tables': dynamodb_tables}


def load_dynamodb_tables(session, data, region, current_aws_account_id, aws_update_tag):
    ingest_table = """
    MERGE (table:DynamoDBTable{id: {Arn}})
    ON CREATE SET table.first seen = timestamp(), table.arn = {Arn}, table.name = {TableName},
    table.region = {Region},
    SET table.lastupdated = {aws_update_tag}, table.rows = {Rows}, table.gsis = {GSIs}, table.size = {Size},
    table.provisioned_throughput_read_capacity_units = ProvisionedThroughputReadCapacityUnits,
    table.provisioned_throughput_write_capacity_units = ProvisionedThroughputWriteCapacityUnits
    WITH table
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(table)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for table in data["Tables"]:
        arn = "arn:aws:dynamodb:{0}:{1}:table/{2}".format(region, current_aws_account_id, table['TableName'])
        session.run(
            ingest_table,
            Arn=arn,
            TableName=table['TableName'],
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
            Rows=table['Rows'],
            Size=table['Size'],
            ProvisionedThroughputReadCapacityUnits=table['ProvisionedThroughputReadCapacityUnits'],
            ProvisionedThroughputWriteCapacityUnits=table['ProvisionedThroughputWriteCapacityUnits'],
        )
        load_gsi(session, data, region, current_aws_account_id, aws_update_tag, table)


def load_gsi(session, data, region, current_aws_account_id, aws_update_tag, table):
    ingest_gsi = """
    MERGE (gsi:DynamoDBTableGSI{id: {Arn}})
    ON CREATE SET gsi.first seen = timestampe(), gsi.arn = {Arn}, gsi.name = {GSIName},
    gsi.region = {Region},
    SET gsi.lastupdate = {aws_update_tag},
    gsi.provisioned_throughput_read_capacity_units = ProvisionedThroughputReadCapacityUnits,
    gsi.provisioned_throughput_write_capacity_units = ProvisionedThroughputWriteCapacityUnits,
    WITH gsi
    MATCH (table:DynamoDBTable{name: {TableName})
    MERGE (table)-[g:GSI]->(gsi)
    ON CREATE SET g.firstseen = timestamp()
    SET g.lastupdated = {aws_update_tag}
    """

    for gsi in table["GSIs"]:
        session.run(
            ingest_gsi,
            Arn=gsi['IndexArn'],
            GSIName=gsi['GSIName'],
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
            Table=table['TableName'],
            ProvisionedThroughputReadCapacityUnits=gsi['ProvisionedThroughputReadCapacityUnits'],
            ProvisionedThroughputWriteCapacityUnits=gsi['ProvisionedThroughputWriteCapacityUnits'],
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

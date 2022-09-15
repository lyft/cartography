import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_dynamodb_tables(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('dynamodb', region_name=region)
    paginator = client.get_paginator('list_tables')
    dynamodb_tables = []
    for page in paginator.paginate():
        for table_name in page['TableNames']:
            dynamodb_tables.append(client.describe_table(TableName=table_name))
    return dynamodb_tables


@timeit
def load_dynamodb_tables(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_table = """
    MERGE (table:DynamoDBTable{id: $Arn})
    ON CREATE SET table.firstseen = timestamp(), table.arn = $Arn, table.name = $TableName,
    table.region = $Region
    SET table.lastupdated = $aws_update_tag, table.rows = $Rows, table.size = $Size,
    table.provisioned_throughput_read_capacity_units = $ProvisionedThroughputReadCapacityUnits,
    table.provisioned_throughput_write_capacity_units = $ProvisionedThroughputWriteCapacityUnits
    WITH table
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(table)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    for table in data:
        neo4j_session.run(
            ingest_table,
            Arn=table['Table']['TableArn'],
            Region=region,
            ProvisionedThroughputReadCapacityUnits=table['Table']['ProvisionedThroughput']['ReadCapacityUnits'],
            ProvisionedThroughputWriteCapacityUnits=table['Table']['ProvisionedThroughput']['WriteCapacityUnits'],
            Size=table['Table']['TableSizeBytes'],
            TableName=table['Table']['TableName'],
            Rows=table['Table']['ItemCount'],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        load_gsi(neo4j_session, table, region, current_aws_account_id, aws_update_tag)


@timeit
def load_gsi(
    neo4j_session: neo4j.Session, table: Dict, region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_gsi = """
    MERGE (gsi:DynamoDBGlobalSecondaryIndex{id: $Arn})
    ON CREATE SET gsi.firstseen = timestamp(), gsi.arn = $Arn, gsi.name = $GSIName,
    gsi.region = $Region
    SET gsi.lastupdated = $aws_update_tag,
    gsi.provisioned_throughput_read_capacity_units = $ProvisionedThroughputReadCapacityUnits,
    gsi.provisioned_throughput_write_capacity_units = $ProvisionedThroughputWriteCapacityUnits
    WITH gsi
    MATCH (table:DynamoDBTable{arn: $TableArn})
    MERGE (table)-[r:GLOBAL_SECONDARY_INDEX]->(gsi)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    for gsi in table['Table'].get('GlobalSecondaryIndexes', []):
        neo4j_session.run(
            ingest_gsi,
            TableArn=table['Table']['TableArn'],
            Arn=gsi['IndexArn'],
            Region=region,
            ProvisionedThroughputReadCapacityUnits=gsi['ProvisionedThroughput']['ReadCapacityUnits'],
            ProvisionedThroughputWriteCapacityUnits=gsi['ProvisionedThroughput']['WriteCapacityUnits'],
            GSIName=gsi['IndexName'],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_dynamodb_tables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_dynamodb_tables_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_dynamodb_tables(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing DynamoDB for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_dynamodb_tables(boto3_session, region)
        load_dynamodb_tables(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_dynamodb_tables(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    sync_dynamodb_tables(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters,
    )
    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='DynamoDBTable',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

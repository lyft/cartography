import logging
import resource
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
import uuid

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.dynamodb.gsi import DynamoDBGSISchema
from cartography.models.aws.dynamodb.tables import DynamoDBTableSchema
import cartography.intel.aws.util.common as filterfn
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.util import dict_value_to_str

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_dynamodb_tables(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('dynamodb', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('list_tables')
    dynamodb_tables = []
    for page in paginator.paginate():
        for table_name in page['TableNames']:
            dynamodb_tables.append(client.describe_table(TableName=table_name))
    return dynamodb_tables


@timeit
def transform_dynamodb_tables(dynamodb_tables: List, region: str) -> Any:
    ddb_table_data: List[Dict[str, Any]] = []
    ddb_gsi_data: List[Dict[str, Any]] = []

    for table in dynamodb_tables:
        ddb_table_data.append({
            'Arn': table['Table']['TableArn'],
            'TableName': table['Table']['TableName'],
            'Region': region,
            'Rows': table['Table']['ItemCount'],
            'Size': table['Table']['TableSizeBytes'],
            'ProvisionedThroughputReadCapacityUnits': table['Table']['ProvisionedThroughput']['ReadCapacityUnits'],
            'ProvisionedThroughputWriteCapacityUnits': table['Table']['ProvisionedThroughput']['WriteCapacityUnits'],
        })
        for gsi in table['Table'].get('GlobalSecondaryIndexes', []):
            ddb_gsi_data.append({
                'Arn': gsi['IndexArn'],
                'TableArn': table['Table']['TableArn'],
                'Region': region,
                'ProvisionedThroughputReadCapacityUnits': gsi['ProvisionedThroughput']['ReadCapacityUnits'],
                'ProvisionedThroughputWriteCapacityUnits': gsi['ProvisionedThroughput']['WriteCapacityUnits'],
                'GSIName': gsi['IndexName'],
            })
    return ddb_table_data, ddb_gsi_data


@timeit
def load_dynamodb_tables(
    neo4j_session: neo4j.Session, tables_data: List[Dict[str, Any]], region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_table = """
    MERGE (table:DynamoDBTable{id: {Arn}})
    ON CREATE SET table.firstseen = timestamp(), table.arn = {Arn}, table.name = {TableName},
    table.region = {Region},
    table.borneo_id = apoc.create.uuid()
    SET table.lastupdated = {aws_update_tag}, table.rows = {Rows}, table.size = {Size},
    table.provisioned_throughput_read_capacity_units = {ProvisionedThroughputReadCapacityUnits},
    table.provisioned_throughput_write_capacity_units = {ProvisionedThroughputWriteCapacityUnits},
    table.creationdate = {CreateDate}
    WITH table
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(table)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
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
            CreateDate = dict_value_to_str(table['Table'], 'CreationDateTime')
        )
        load_gsi(neo4j_session, table, region, current_aws_account_id, aws_update_tag)


@timeit
def load_dynamodb_gsi(
    neo4j_session: neo4j.Session, gsi_data: List[Dict[str, Any]], region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_gsi = """
    MERGE (gsi:DynamoDBGlobalSecondaryIndex{id: {Arn}})
    ON CREATE SET gsi.firstseen = timestamp(), gsi.arn = {Arn}, gsi.name = {GSIName},
    gsi.region = {Region},
    gsi.borneo_id = apoc.create.uuid()
    SET gsi.lastupdated = {aws_update_tag},
    gsi.provisioned_throughput_read_capacity_units = {ProvisionedThroughputReadCapacityUnits},
    gsi.provisioned_throughput_write_capacity_units = {ProvisionedThroughputWriteCapacityUnits}
    WITH gsi
    MATCH (table:DynamoDBTable{arn: {TableArn}})
    MERGE (table)-[r:GLOBAL_SECONDARY_INDEX]->(gsi)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
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
            aws_update_tag=aws_update_tag
        )


@timeit
def cleanup_dynamodb_tables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(DynamoDBTableSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(DynamoDBGSISchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_dynamodb_tables(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    resourceFound = False
    for region in regions:
        logger.info("Syncing DynamoDB for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_dynamodb_tables(boto3_session, region)
        if common_job_parameters['aws_resource_name'] is not None:
            logger.info('Filtering to run updation for: %s', common_job_parameters['aws_resource_name'])
            # bucket_data is updated in the function itself
            data = filterfn.filter_resources(data, common_job_parameters['aws_resource_name'], 'dynamodb')
            resourceFound = True
        load_dynamodb_tables(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    if(not resourceFound):
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

import logging
from dataclasses import dataclass
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudwatch_log_groups(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('logs', region_name=region, config=get_botocore_config())
    log_groups: List[Dict] = []
    paginator = client.get_paginator('describe_log_groups')
    for page in paginator.paginate():
        log_group = page['logGroups']
        log_groups.extend(log_group)
    return log_groups


@timeit
def transform_cloudwatch_log_groups(log_groups: List[Dict]) -> List[Dict]:
    for i in range(len(log_groups)):
        if 'creationTime' in log_groups[i]:
            # Convert to seconds from milliseconds
            log_groups[i]['creationTime'] = int(log_groups[i]['creationTime'] / 1000)
    return log_groups


@dataclass(frozen=True)
class CloudWatchLogGroupProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('arn')
    creation_time: PropertyRef = PropertyRef('creationTime')
    data_protection_status: PropertyRef = PropertyRef('dataProtectionStatus')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('arn')
    kms_key_id: PropertyRef = PropertyRef('kmsKeyId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    log_group_name: PropertyRef = PropertyRef('logGroupName')
    metric_filter_count: PropertyRef = PropertyRef('metricFilterCount')
    retention_in_days: PropertyRef = PropertyRef('retentionInDays')
    stored_bytes: PropertyRef = PropertyRef('storedBytes')


@dataclass(frozen=True)
class CloudWatchLogGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudWatchLogGroup)<-[:RESOURCE]-(:AWSAccount)
class CloudWatchLogGroupToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchLogGroupToAWSAccountRelProperties = CloudWatchLogGroupToAWSAccountRelProperties()


@dataclass(frozen=True)
class CloudWatchLogGroupSchema(CartographyNodeSchema):
    label: str = 'CloudWatchLogGroup'
    properties: CloudWatchLogGroupProperties = CloudWatchLogGroupProperties()
    sub_resource_relationship: CloudWatchLogGroupToAWSAccount = CloudWatchLogGroupToAWSAccount()


@timeit
def load_cloudwatch_log_groups(
        neo4j_session: neo4j.Session,
        log_groups: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudwatch log groups into graph.", len(log_groups))

    ingestion_query = build_ingestion_query(CloudWatchLogGroupSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        log_groups,
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running CloudWatch cleanup job.")
    run_cleanup_job('aws_import_cloudwatch_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing cloudwatch log groups for region '%s' in account '%s'.", region, current_aws_account_id)
        log_groups = get_cloudwatch_log_groups(boto3_session, region)
        log_groups = transform_cloudwatch_log_groups(log_groups)
        load_cloudwatch_log_groups(neo4j_session, log_groups, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

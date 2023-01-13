import logging
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import OtherRelationships
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
@aws_handle_regions
def get_cloudwatch_metric_filters(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('logs', region_name=region, config=get_botocore_config())
    metric_filters: List[Dict] = []
    paginator = client.get_paginator('describe_metric_filters')
    for page in paginator.paginate():
        metric_filter = page['metricFilters']
        metric_filters.extend(metric_filter)
    return metric_filters


@timeit
def transform_cloudwatch_metric_filters(
    metric_filters: List[Dict],
    region: str,
    current_aws_account_id: str,
) -> List[Dict]:
    for i in range(len(metric_filters)):
        # Synthetic arn to identify metric filter
        metric_filters[i]['arn'] = \
            f'arn:aws:logs:{region}:{current_aws_account_id}:metric_filter:{metric_filters[i]["filterName"]}'
        # Recreate log group arn for relationship between metric filter and log group
        metric_filters[i]['logGroupArn'] = \
            f'arn:aws:logs:{region}:{current_aws_account_id}:log-group:{metric_filters[i]["logGroupName"]}:*'
        if 'creationTime' in metric_filters[i]:
            # Convert to seconds from milliseconds
            metric_filters[i]['creationTime'] = int(metric_filters[i]['creationTime'] / 1000)
        if 'metricTransformations' in metric_filters[i] and len(metric_filters[i]['metricTransformations']) > 0:
            # Add metricTransformationName
            metric_filters[i]['metricTransformationName'] = metric_filters[i]['metricTransformations'][0]['metricName']
    return metric_filters


@timeit
def load_cloudwatch_metric_filters(
        neo4j_session: neo4j.Session,
        metric_filters: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudwatch metric filters into graph.", len(metric_filters))

    ingestion_query = build_ingestion_query(CloudWatchMetricFilterSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        metric_filters,
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


@dataclass(frozen=True)
class CloudWatchMetricFilterProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('arn')
    creation_time: PropertyRef = PropertyRef('creationTime')
    filter_name: PropertyRef = PropertyRef('filterName')
    filter_pattern: PropertyRef = PropertyRef('filterPattern')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('arn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    log_group_arn: PropertyRef = PropertyRef('logGroupArn')
    log_group_name: PropertyRef = PropertyRef('logGroupName')
    metric_transformation_name: PropertyRef = PropertyRef('metricTransformationName')


@dataclass(frozen=True)
class CloudWatchMetricFilterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudWatchMetricFilter)<-[:RESOURCE]-(:AWSAccount)
class CloudWatchMetricFilterToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchMetricFilterToAWSAccountRelProperties = CloudWatchMetricFilterToAWSAccountRelProperties()


@dataclass(frozen=True)
class CloudWatchMetricFilterToCloudWatchLogGroupRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudWatchMetricFilter)<-[:HAS_METRIC_FILTER]-(:CloudWatchLogGroup)
class CloudWatchMetricFilterToCloudWatchLogGroup(CartographyRelSchema):
    target_node_label: str = 'CloudWatchLogGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('logGroupArn')})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_METRIC_FILTER"
    properties: CloudWatchMetricFilterToCloudWatchLogGroupRelProps = \
        CloudWatchMetricFilterToCloudWatchLogGroupRelProps()


@dataclass(frozen=True)
class CloudWatchMetricFilterSchema(CartographyNodeSchema):
    label: str = 'CloudWatchMetricFilter'
    properties: CloudWatchMetricFilterProperties = CloudWatchMetricFilterProperties()
    sub_resource_relationship: CloudWatchMetricFilterToAWSAccount = CloudWatchMetricFilterToAWSAccount()
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            CloudWatchMetricFilterToCloudWatchLogGroup(),
        ],
    )


@timeit
@aws_handle_regions
def get_cloudwatch_alarms(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('cloudwatch', region_name=region, config=get_botocore_config())
    alarms: List[Dict] = []
    paginator = client.get_paginator('describe_alarms')
    for page in paginator.paginate():
        alarm = page['MetricAlarms']
        alarms.extend(alarm)
    return alarms


@timeit
def load_cloudwatch_alarms(
        neo4j_session: neo4j.Session,
        alarms: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudwatch alarms into graph.", len(alarms))

    ingestion_query = build_ingestion_query(CloudWatchAlarmSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        alarms,
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


@dataclass(frozen=True)
class CloudWatchAlarmProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('AlarmArn')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('AlarmArn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    metric_name: PropertyRef = PropertyRef('MetricName')
    name: PropertyRef = PropertyRef('AlarmName')


@dataclass(frozen=True)
class CloudWatchAlarmToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudWatchAlarm)<-[:RESOURCE]-(:AWSAccount)
class CloudWatchAlarmToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchAlarmToAWSAccountRelProperties = CloudWatchAlarmToAWSAccountRelProperties()


@dataclass(frozen=True)
class CloudWatchAlarmSchema(CartographyNodeSchema):
    label: str = 'CloudWatchAlarm'
    properties: CloudWatchAlarmProperties = CloudWatchAlarmProperties()
    sub_resource_relationship: CloudWatchAlarmToAWSAccount = CloudWatchAlarmToAWSAccount()


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running CloudWatch cleanup job.")
    run_cleanup_job('aws_import_cloudwatch_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    # TODO: Ideally, we should have log group, metric filter, metric, and alarm nodes with edges between them.
    for region in regions:
        logger.info(
            "Syncing cloudwatch log groups, metric filters, and alarms for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        log_groups = get_cloudwatch_log_groups(boto3_session, region)
        log_groups = transform_cloudwatch_log_groups(log_groups)
        load_cloudwatch_log_groups(neo4j_session, log_groups, current_aws_account_id, update_tag)

        metric_filters = get_cloudwatch_metric_filters(boto3_session, region)
        metric_filters = transform_cloudwatch_metric_filters(metric_filters, region, current_aws_account_id)
        load_cloudwatch_metric_filters(neo4j_session, metric_filters, current_aws_account_id, update_tag)

        alarms = get_cloudwatch_alarms(boto3_session, region)
        load_cloudwatch_alarms(neo4j_session, alarms, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

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
from cartography.util import dict_date_to_epoch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudtrail_trails(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('cloudtrail', region_name=region, config=get_botocore_config())
    trails: List[Dict] = client.describe_trails()['trailList']
    for i in range(len(trails)):
        trail_status = client.get_trail_status(Name=trails[i]['TrailARN'])
        trails[i]['IsLogging'] = trail_status['IsLogging'] if 'IsLogging' in trail_status else None
        trails[i]['LatestCloudWatchLogsDeliveryTime'] = (
            trail_status['LatestCloudWatchLogsDeliveryTime']
            if 'LatestCloudWatchLogsDeliveryTime' in trail_status
            else None
        )
    return trails


@timeit
def transform_trail_and_related_objects(trails: List[Dict]) -> Tuple[List, List, List]:
    s3_buckets: List[Dict] = []
    log_groups: List[Dict] = []
    for i in range(len(trails)):
        trails[i]['LatestCloudWatchLogsDeliveryTime'] = dict_date_to_epoch(
            trails[i], 'LatestCloudWatchLogsDeliveryTime',
        )
        if 'S3BucketName' in trails[i] and len(trails[i]['S3BucketName']) > 0:
            s3_buckets.append({
                'S3BucketName': trails[i]['S3BucketName'],
            })
        if 'CloudWatchLogsLogGroupArn' in trails[i] and len(trails[i]['CloudWatchLogsLogGroupArn']) > 0:
            log_groups.append({
                'CloudWatchLogsLogGroupArn': trails[i]['CloudWatchLogsLogGroupArn'],
            })
    return trails, s3_buckets, log_groups


@timeit
@aws_handle_regions
def get_cloudtrail_event_selectors(boto3_session: boto3.session.Session, region: str, trail: Dict) -> List[Dict]:
    client = boto3_session.client('cloudtrail', region_name=region, config=get_botocore_config())
    return client.get_event_selectors(TrailName=trail['TrailARN']).get('EventSelectors', [])


@timeit
def transform_event_selectors(event_selectors: List[Dict], trail: Dict) -> List[Dict]:
    for i in range(len(event_selectors)):
        event_selectors[i]['TrailARN'] = trail['TrailARN']
        if 'DataResources' in event_selectors[i]:
            event_selectors[i]['DataResources'] = json.dumps(event_selectors[i]['DataResources'])
        if 'ExcludeManagementEventSources' in event_selectors[i]:
            event_selectors[i]['ExcludeManagementEventSources'] = json.dumps(
                event_selectors[i]['ExcludeManagementEventSources'],
            )
        id_data = "{}:{}:{}:{}:{}".format(
            event_selectors[i].get('TrailARN'),
            event_selectors[i].get('ReadWriteType'),
            event_selectors[i].get('IncludeManagementEvents'),
            event_selectors[i].get('DataResources'),
            event_selectors[i].get('ExcludeManagementEventSources'),
        )
        event_selectors[i]['id'] = hashlib.sha256(id_data.encode("utf8")).hexdigest()
    return event_selectors


@dataclass(frozen=True)
class CloudTrailNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('TrailARN')
    cloud_watch_logs_log_group_arn: PropertyRef = PropertyRef('CloudWatchLogsLogGroupArn')
    cloud_watch_logs_role_arn: PropertyRef = PropertyRef('CloudWatchLogsRoleArn')
    firstseen: PropertyRef = PropertyRef('firstseen')
    has_custom_event_selectors: PropertyRef = PropertyRef('HasCustomEventSelectors')
    has_insight_selectors: PropertyRef = PropertyRef('HasInsightSelectors')
    home_region: PropertyRef = PropertyRef('HomeRegion')
    id: PropertyRef = PropertyRef('TrailARN')
    include_global_service_events: PropertyRef = PropertyRef('IncludeGlobalServiceEvents')
    is_logging: PropertyRef = PropertyRef('IsLogging')
    is_multi_region_trail: PropertyRef = PropertyRef('IsMultiRegionTrail')
    is_organization_trail: PropertyRef = PropertyRef('IsOrganizationTrail')
    kms_key_id: PropertyRef = PropertyRef('KmsKeyId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    latest_cloud_watch_logs_delivery_time: PropertyRef = PropertyRef('LatestCloudWatchLogsDeliveryTime')
    log_file_validation_enabled: PropertyRef = PropertyRef('LogFileValidationEnabled')
    name: PropertyRef = PropertyRef('Name')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    s3_bucket_name: PropertyRef = PropertyRef('S3BucketName')
    s3_key_prefix: PropertyRef = PropertyRef('S3KeyPrefix')
    sns_topic_name: PropertyRef = PropertyRef('SnsTopicName')
    sns_topic_arn: PropertyRef = PropertyRef('SnsTopicARN')


@dataclass(frozen=True)
class CloudTrailToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudTrail)<-[:RESOURCE]-(:AWSAccount)
class CloudTrailToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudTrailToAWSAccountRelProperties = CloudTrailToAWSAccountRelProperties()


@dataclass(frozen=True)
class CloudTrailToS3BucketRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudTrail)-[:DELIVERS_TO]->(:S3Bucket)
class CloudTrailToS3Bucket(CartographyRelSchema):
    target_node_label: str = 'S3Bucket'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('S3BucketName')})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: CloudTrailToS3BucketRelProps = CloudTrailToS3BucketRelProps()


@dataclass(frozen=True)
class CloudTrailToCloudWatchLogGroupRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudTrail)-[:DELIVERS_TO]->(:CloudWatchLogGroup)
class CloudTrailToCloudWatchLogGroup(CartographyRelSchema):
    target_node_label: str = 'CloudWatchLogGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('CloudWatchLogsLogGroupArn')})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: CloudTrailToCloudWatchLogGroupRelProps = CloudTrailToCloudWatchLogGroupRelProps()


@dataclass(frozen=True)
class CloudTrailSchema(CartographyNodeSchema):
    label: str = 'CloudTrail'
    properties: CloudTrailNodeProperties = CloudTrailNodeProperties()
    sub_resource_relationship: CloudTrailToAWSAccount = CloudTrailToAWSAccount()
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            CloudTrailToS3Bucket(),
            CloudTrailToCloudWatchLogGroup(),
        ],
    )


@timeit
def load_cloudtrail_trails(
        neo4j_session: neo4j.Session,
        trails: List[Dict],
        region: str,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudtrail trails for region '%s' into graph.", len(trails), region)

    ingestion_query = build_ingestion_query(CloudTrailSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        trails,
        lastupdated=aws_update_tag,
        Region=region,
        AccountId=current_aws_account_id,
    )


@dataclass(frozen=True)
class S3BucketNodeProperties(CartographyNodeProperties):
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('S3BucketName')
    name: PropertyRef = PropertyRef('S3BucketName')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class S3BucketSchema(CartographyNodeSchema):
    label: str = 'S3Bucket'
    properties: S3BucketNodeProperties = S3BucketNodeProperties()


@timeit
def load_cloudtrail_s3_buckets(
        neo4j_session: neo4j.Session,
        s3_buckets: List[Dict],
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudtrail s3 buckets into graph.", len(s3_buckets))

    ingestion_query = build_ingestion_query(S3BucketSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        s3_buckets,
        lastupdated=aws_update_tag,
    )


@dataclass(frozen=True)
class CloudWatchLogGroupNodeProperties(CartographyNodeProperties):
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('CloudWatchLogsLogGroupArn')
    arn: PropertyRef = PropertyRef('CloudWatchLogsLogGroupArn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogGroupSchema(CartographyNodeSchema):
    label: str = 'CloudWatchLogGroup'
    properties: CloudWatchLogGroupNodeProperties = CloudWatchLogGroupNodeProperties()


@timeit
def load_cloudtrail_log_groups(
        neo4j_session: neo4j.Session,
        log_groups: List[Dict],
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudwatch log groups into graph.", len(log_groups))

    ingestion_query = build_ingestion_query(CloudWatchLogGroupSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        log_groups,
        lastupdated=aws_update_tag,
    )


@dataclass(frozen=True)
class CloudTrailEventSelectorNodeProperties(CartographyNodeProperties):
    data_resources: PropertyRef = PropertyRef('DataResources')
    exclude_management_event_sources: PropertyRef = PropertyRef('ExcludeManagementEventSources')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('id')
    include_management_events: PropertyRef = PropertyRef('IncludeManagementEvents')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    read_write_type: PropertyRef = PropertyRef('ReadWriteType')


@dataclass(frozen=True)
class CloudTrailEventSelectorToCloudTrailRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudTrailEventSelector)-[:APPLIES_TO]->(:CloudTrail)
class CloudTrailEventSelectorToCloudTrail(CartographyRelSchema):
    target_node_label: str = 'CloudTrail'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('TrailARN')})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: CloudTrailEventSelectorToCloudTrailRelProps = CloudTrailEventSelectorToCloudTrailRelProps()


@dataclass(frozen=True)
class CloudTrailEventSelectorSchema(CartographyNodeSchema):
    label: str = 'CloudTrailEventSelector'
    properties: CloudTrailEventSelectorNodeProperties = CloudTrailEventSelectorNodeProperties()
    other_relationships: Optional[OtherRelationships] = OtherRelationships([
        CloudTrailEventSelectorToCloudTrail(),
    ])


@timeit
def load_cloudtrail_event_selectors(
        neo4j_session: neo4j.Session,
        event_selectors: List[Dict],
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d cloudwatch event selectors into graph.", len(event_selectors))

    ingestion_query = build_ingestion_query(CloudTrailEventSelectorSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        event_selectors,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running CloudTrail cleanup job.")
    run_cleanup_job('aws_import_cloudtrail_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing cloudtrail trails for region '%s' in account '%s'.", region, current_aws_account_id)

        trails = get_cloudtrail_trails(boto3_session, region)
        trails, s3_buckets, log_groups = transform_trail_and_related_objects(trails)

        transformed_event_selectors: List[Dict] = []
        for trail in trails:
            event_selectors = get_cloudtrail_event_selectors(boto3_session, region, trail)
            event_selectors = transform_event_selectors(event_selectors, trail)
            transformed_event_selectors.extend(event_selectors)

        load_cloudtrail_s3_buckets(neo4j_session, s3_buckets, update_tag)
        load_cloudtrail_log_groups(neo4j_session, log_groups, update_tag)
        load_cloudtrail_trails(neo4j_session, trails, region, current_aws_account_id, update_tag)
        load_cloudtrail_event_selectors(neo4j_session, transformed_event_selectors, update_tag)

    cleanup(neo4j_session, common_job_parameters)

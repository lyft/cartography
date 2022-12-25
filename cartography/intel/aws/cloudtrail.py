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
def transform_trail_and_related_objects(trails: List[Dict]) -> Tuple[List, List]:
    s3_buckets: List[Dict] = []
    for i in range(len(trails)):
        trails[i]['Id'] = trails[i]['TrailARN']
        trails[i]['LatestCloudWatchLogsDeliveryTime'] = dict_date_to_epoch(
            trails[i], 'LatestCloudWatchLogsDeliveryTime',
        )
        if 'S3BucketName' in trails[i] and len(trails[i]['S3BucketName']) > 0:
            s3_buckets.append({
                'Id': trails[i]['S3BucketName'],
                'Name': trails[i]['S3BucketName'],
            })
    return trails, s3_buckets


@dataclass(frozen=True)
class CloudTrailNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('TrailARN')
    cloud_watch_logs_log_group_arn: PropertyRef = PropertyRef('CloudWatchLogsLogGroupArn')
    cloud_watch_logs_role_arn: PropertyRef = PropertyRef('CloudWatchLogsRoleArn')
    firstseen: PropertyRef = PropertyRef('firstseen')
    has_custom_event_selectors: PropertyRef = PropertyRef('HasCustomEventSelectors')
    has_insight_selectors: PropertyRef = PropertyRef('HasInsightSelectors')
    home_region: PropertyRef = PropertyRef('HomeRegion')
    id: PropertyRef = PropertyRef('Id')
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
class CloudTrailSchema(CartographyNodeSchema):
    label: str = 'CloudTrail'
    properties: CloudTrailNodeProperties = CloudTrailNodeProperties()
    sub_resource_relationship: CloudTrailToAWSAccount = CloudTrailToAWSAccount()
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            CloudTrailToS3Bucket(),
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
    id: PropertyRef = PropertyRef('Id')
    name: PropertyRef = PropertyRef('Name')
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
        trails, s3_buckets = transform_trail_and_related_objects(trails)
        load_cloudtrail_s3_buckets(neo4j_session, s3_buckets, update_tag)
        load_cloudtrail_trails(neo4j_session, trails, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

import time
import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_trails(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('cloudtrail', region_name=region)
    response = client.describe_trails(includeShadowTrails=False)
    return response.get('trailList', [])


@timeit
def transform_trails(trails: List[Dict]) -> List[Dict]:
    for trail in trails:
        trail['consolelink'] = aws_console_link.get_console_link(arn=trail['TrailARN'])

    return trails


@timeit
def load_trails(neo4j_session: neo4j.Session, trails: Dict, current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (trail:AWSCloudTrailTrail{id: record.TrailARN})
    ON CREATE SET trail.firstseen = timestamp(),
        trail.arn = record.TrailARN
    SET trail.lastupdated = $aws_update_tag,
        trail.name = record.Name,
        trail.arn = record.TrailARN,
        trail.consolelink = record.consolelink,
        trail.region = record.HomeRegion,
        trail.is_multi_region_trail = record.IsMultiRegionTrail,
        trail.is_organization_trail = record.IsOrganizationTrail,
        trail.s3bucket_name = record.S3BucketName,
        trail.include_global_service_events = record.IncludeGlobalServiceEvents,
        trail.log_file_validation_enabled = record.LogFileValidationEnabled,
        trail.has_custom_event_selectors = record.HasCustomEventSelectors,
        trail.has_insight_selectors = record.HasInsightSelectors
    WITH trail
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(trail)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        query,
        Records=trails,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudtrail_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing CloudTrail for account '%s', at %s.", current_aws_account_id, tic)

    trails = []
    for region in regions:
        logger.info("Syncing CloudTrail for region '%s' in account '%s'.", region, current_aws_account_id)

        trails.extend(get_trails(boto3_session, region))

    logger.info(f"Total CloudTrail Trails: {len(trails)}")

    if common_job_parameters.get('pagination', {}).get('cloudtrail', None):
        pageNo = common_job_parameters.get("pagination", {}).get("cloudtrail", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("cloudtrail", None)["pageSize"]
        totalPages = len(trails) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for cloudtrail trails {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('cloudtrail', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('cloudtrail', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('cloudtrail', {})['pageSize']
        if page_end > len(trails) or page_end == len(trails):
            trails = trails[page_start:]

        else:
            has_next_page = True
            trails = trails[page_start:page_end]
            common_job_parameters['pagination']['cloudtrail']['hasNextPage'] = has_next_page

    trails = transform_trails(trails)

    load_trails(neo4j_session, trails, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process CloudTrail: {toc - tic:0.4f} seconds")

import json
import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_cloudfront_distributions(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3_session.client('cloudfront')
    paginator = client.get_paginator('list_distributions')
    cloudfront_distributions = []
    for page in paginator.paginate():
        for distribution in page['DistributionList']['Items']:
            cloudfront_distributions.append(distribution)
    return cloudfront_distributions


@timeit
def load_distribution_origin(
        neo4j_session: neo4j.Session,
        distribution_arn: str,
        origins: Dict,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_definitions = """
        MERGE (d:CloudFrontDistributionOrigin{id: $distribution_arn + "-" + $origin.Id})
        ON CREATE SET d.firstseen = timestamp()
        SET
            d.domain_name = $origin.DomainName,
            d.origin_path = $origin.OriginPath,
            d.custom_headers = $origin.CustomHeaders.Items,
            d.connection_timeout = $origin.ConnectionTimeout,
            d.connection_attempts = $origin.ConnectionAttempts,
            d.origin_access_control_id = $origin.OriginAccessControlId,
            d.originshield_enabled = $origin.OriginShield.Enabled,
            d.originshield_region = $origin.OriginShield.OriginShieldRegion,
            d.s3_origin_enabled = $origin.S3OriginConfig.S3OriginConfigEnabled,
            d.custom_origin_enabled = $origin.CustomOriginConfig.CustomOriginConfigEnabled,
            d.s3_origin_config = $origin.S3OriginConfig_Data,
            d.custom_origin_config = $origin.CustomOriginConfig_Data,
            d.lastupdated = $aws_update_tag
        WITH d
        MATCH (td:CloudFrontDistribution{arn: $distribution_arn})
        MERGE (td)-[r:HAS_ORIGIN]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """

    for origin in origins:
        if origin["CustomHeaders"]["Quantity"] == 0:
            origin["CustomHeaders"]["Items"] = []

        origin["CustomHeaders"]["Items"] = json.dumps(origin["CustomHeaders"]["Items"])

        if not origin["OriginShield"]["Enabled"]:
            origin["OriginShield"]["OriginShieldRegion"] = ""

        if "S3OriginConfig" not in origin:
            origin["S3OriginConfig"] = {}
            origin["S3OriginConfig"]["S3OriginConfigEnabled"] = False
        else:
            origin["S3OriginConfig"]["S3OriginConfigEnabled"] = True

        if "CustomOriginConfig" not in origin:
            origin["CustomOriginConfig"] = {}
            origin["CustomOriginConfig"]["CustomOriginConfigEnabled"] = False
        else:
            origin["CustomOriginConfig"]["CustomOriginConfigEnabled"] = True

        origin["S3OriginConfig_Data"] = json.dumps(origin["S3OriginConfig"])
        origin["CustomOriginConfig_Data"] = json.dumps(origin["CustomOriginConfig"])

        neo4j_session.run(
            ingest_definitions,
            distribution_arn=distribution_arn,
            origin=origin,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_cloudfront_distributions(
        neo4j_session: neo4j.Session,
        data: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_distribution = """
        MERGE (d:CloudFrontDistribution{id: $distribution.ARN})
        ON CREATE SET d.firstseen = timestamp()
        SET d.arn = $distribution.ARN,
            d.comment = $distribution.Comment,
            d.domain_name = $distribution.DomainName,
            d.enabled = $distribution.Enabled,
            d.http_version = $distribution.HttpVersion,
            d.is_ipv6_enabled = $distribution.IsIPV6Enabled,
            d.last_modified_time = $distribution.LastModifiedTime,
            d.status = $distribution.Status,
            d.web_acl_id = $distribution.WebACLId,
            d.geo_restriction_type = $distribution.Restrictions.GeoRestriction.RestrictionType,
            d.geo_restriction_quantity = $distribution.Restrictions.GeoRestriction.Quantity,
            d.geo_restriction_items = $distribution.Restrictions.GeoRestriction.Items,
            d.aliases_quantity = $distribution.Aliases.Quantity,
            d.aliases_items = $distribution.Aliases.Items,
            d.origins_quantity = $distribution.Origins.Quantity,
            d.origin_groups = $distribution.OriginGroups,
            d.cache_behaviors = $distribution.CacheBehaviors,
            d.default_cache_behavior = $distribution.DefaultCacheBehavior,
            d.custom_error_responses = $distribution.CustomErrorResponses,
            d.viewer_certificate = $distribution.ViewerCertificate,
            d.lastupdated = $aws_update_tag
        WITH d
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    for distribution in data:
        distribution["LastModifiedTime"] = dict_date_to_epoch(distribution, 'LastModifiedTime')

        if distribution["Restrictions"]["GeoRestriction"]["Quantity"] == 0:
            distribution["Restrictions"]["GeoRestriction"]["Items"] = []

        if distribution["Aliases"]["Quantity"] == 0:
            distribution["Aliases"]["Items"] = []

        distribution["OriginGroups"] = json.dumps(distribution["OriginGroups"])
        distribution["CacheBehaviors"] = json.dumps(distribution["CacheBehaviors"])
        distribution["DefaultCacheBehavior"] = json.dumps(distribution["DefaultCacheBehavior"])
        distribution["CustomErrorResponses"] = json.dumps(distribution["CustomErrorResponses"])
        distribution["ViewerCertificate"] = json.dumps(distribution["ViewerCertificate"])

        neo4j_session.run(
            ingest_distribution,
            distribution=distribution,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        load_distribution_origin(
            neo4j_session, distribution["ARN"],
            distribution["Origins"]["Items"],
            current_aws_account_id,
            aws_update_tag,
        )


@timeit
def sync_cloudfront_distributions(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    distributions_data = get_cloudfront_distributions(boto3_session)
    load_cloudfront_distributions(neo4j_session, distributions_data, current_aws_account_id, aws_update_tag)


@timeit
def cleanup_cloudfront(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudfront_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict,
) -> None:
    logger.info(f"Syncing AWS Cloudfront  in account '{current_aws_account_id}'.")
    sync_cloudfront_distributions(neo4j_session, boto3_session, current_aws_account_id, update_tag)
    cleanup_cloudfront(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='CloudFrontDistribution',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

import time
import logging
from typing import Dict
from typing import List
from botocore.exceptions import ClientError

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudfront_distributions(boto3_session: boto3.session.Session) -> List[Dict]:
    distributions = []
    try:
        client = boto3_session.client('cloudfront')
        paginator = client.get_paginator('list_distributions')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            distributions.extend(page.get('DistributionList', {}).get('Items', []))
        for distribution in distributions:
            distribution['region'] = 'global'

        return distributions

    except ClientError as e:
        logger.error(f'Failed to call CloudFront list_distributions: {e}')
        return distributions


def load_cloudfront_distributions(session: neo4j.Session, distributions: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_cloudfront_distributions_tx, distributions, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudfront_distributions_tx(tx: neo4j.Transaction, distributions: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (distribution:AWSCloudfrontDistribution{id: record.ARN})
    ON CREATE SET distribution.firstseen = timestamp(),
        distribution.arn = record.ARN
    SET distribution.lastupdated = $aws_update_tag,
        distribution.name = record.Id,
        distribution.region = record.region,
        distribution.status = record.Status,
        distribution.domain_name = record.DomainName,
        distribution.comment = record.Comment,
        distribution.price_class = record.PriceClass,
        distribution.enabled = record.Enabled,
        distribution.web_acl_id = record.WebACLId,
        distribution.is_ipv6_enabled = record.IsIPV6Enabled,
        distribution.http_version = record.HttpVersion
    WITH distribution
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(distribution)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=distributions,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudfront_distributions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudfront_distributions_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Cloudfront for account '%s', at %s.", current_aws_account_id, tic)

    distributions = get_cloudfront_distributions(boto3_session)

    logger.info(f"Total Cloudfront Distributions: {len(distributions)}")

    if common_job_parameters.get('pagination', {}).get('cloudfront', None):
        pageNo = common_job_parameters.get("pagination", {}).get("cloudfront", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("cloudfront", None)["pageSize"]
        totalPages = len(distributions) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for Cloudfront distributions {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('cloudfront', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('cloudfront', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('cloudfront', {})['pageSize']
        if page_end > len(distributions) or page_end == len(distributions):
            distributions = distributions[page_start:]

        else:
            has_next_page = True
            distributions = distributions[page_start:page_end]
            common_job_parameters['pagination']['cloudfront']['hasNextPage'] = has_next_page

    load_cloudfront_distributions(neo4j_session, distributions, current_aws_account_id, update_tag)

    cleanup_cloudfront_distributions(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Cloudfront: {toc - tic:0.4f} seconds")

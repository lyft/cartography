import time
import logging
from typing import Dict
from typing import List
from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError
from botocore.client import Config

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
def get_ses_identity(boto3_session: boto3.session.Session, region: str, current_aws_account_id: str,) -> List[Dict]:
    identity_names = []
    resources = []
    try:
        config = Config(connect_timeout=10, retries={'max_attempts': 0})

        client = boto3_session.client('ses', config=config, region_name=region)
        paginator = client.get_paginator('list_identities')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            identity_names.extend(page.get('Identities', []))

        identities = []
        for identity_name in identity_names:
            identities.append({'name': identity_name})
        dkim_attributes = client.get_identity_dkim_attributes(Identities=identity_names).get('DkimAttributes', {})

        identity_verifications = client.get_identity_verification_attributes(
            Identities=identity_names).get('VerificationAttributes', {})

        for identity in identities:
            identity['arn'] = f"arn:aws:ses:{region}:{current_aws_account_id}:identity/{identity['name']}"
            identity['consolelink'] = aws_console_link.get_console_link(arn=identity['arn'])
            identity['region'] = region
            identity['dkim'] = dkim_attributes.get(identity['name'], {})
            identity['verification'] = identity_verifications.get(identity['name'], {})

            resources.append(identity)

        return resources

    except (ClientError, ConnectTimeoutError, EndpointConnectionError) as e:
        logger.error(f'Failed to call SES list_identities: {region} - {e}')
        return resources


def load_ses_identity(session: neo4j.Session, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_ses_identity_tx, identities, current_aws_account_id, aws_update_tag)


@timeit
def _load_ses_identity_tx(tx: neo4j.Transaction, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (identity:AWSSESIdentity{id: record.arn})
    ON CREATE SET identity.firstseen = timestamp(),
        identity.arn = record.arn
    SET identity.lastupdated = {aws_update_tag},
        identity.name = record.name,
        identity.region = record.region,
        identity.consolelink = record.consolelink,
        identity.dkim_enabled = record.dkim.DkimEnabled,
        identity.dkim_verification_status = record.dkim.DkimVerificationStatus,
        identity.verification_status = record.verification.VerificationStatus
    WITH identity
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(identity)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=identities,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_ses_identities(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ses_identity_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,


) -> None:
    tic = time.perf_counter()

    logger.info("Syncing SES for account '%s', at %s.", current_aws_account_id, tic)

    identities = []
    for region in regions:
        logger.info("Syncing SES for region '%s' in account '%s'.", region, current_aws_account_id)

        identities.extend(get_ses_identity(boto3_session, region, current_aws_account_id))

    logger.info(f"Total SES Identities: {len(identities)}")

    if common_job_parameters.get('pagination', {}).get('ses', None):
        pageNo = common_job_parameters.get("pagination", {}).get("ses", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("ses", None)["pageSize"]
        totalPages = len(identities) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for SES identities {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('ses', {})[
            'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('ses', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('ses', {})['pageSize']
        if page_end > len(identities) or page_end == len(identities):
            identities = identities[page_start:]

        else:
            has_next_page = True
            identities = identities[page_start:page_end]
            common_job_parameters['pagination']['ses']['hasNextPage'] = has_next_page

    load_ses_identity(neo4j_session, identities, current_aws_account_id, update_tag)
    cleanup_ses_identities(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process SES Service: {toc - tic:0.4f} seconds")

import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_ses_identity(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    identity_names = []
    try:
        client = boto3_session.client('ses', region_name=region, config=get_botocore_config())
        paginator = client.get_paginator('list_identities')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            identity_names.extend(page.get('Identities', []))

        return identity_names

    except (ClientError, ConnectTimeoutError, EndpointConnectionError) as e:
        logger.error(f'Failed to call SES list_identities: {region} - {e}')
        return identity_names


@timeit
def transform_identities(boto3_session: boto3.session.Session, idsnames: List[Dict], region: str, current_aws_account_id: str) -> List[Dict]:
    identities = []
    resources = []
    try:
        client = boto3_session.client('ses', region_name=region, config=get_botocore_config())
        for identity_name in idsnames:
            identities.append({'name': identity_name})
        dkim_attributes = client.get_identity_dkim_attributes(Identities=idsnames).get('DkimAttributes', {})

        identity_verifications = client.get_identity_verification_attributes(
            Identities=idsnames,
        ).get('VerificationAttributes', {})

        for identity in identities:
            identity['arn'] = f"arn:aws:ses:{region}:{current_aws_account_id}:identity/{identity['name']}"
            identity['consolelink'] = aws_console_link.get_console_link(arn=identity['arn'])
            identity['region'] = region
            identity['dkim'] = dkim_attributes.get(identity['name'], {})
            identity['verification'] = identity_verifications.get(identity['name'], {})

            resources.append(identity)
    except (ClientError, ConnectTimeoutError, EndpointConnectionError) as e:
        logger.error(f'Failed to call SES list_identities: {region} - {e}')

    return resources


def load_ses_identity(session: neo4j.Session, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_ses_identity_tx, identities, current_aws_account_id, aws_update_tag)


@timeit
def _load_ses_identity_tx(tx: neo4j.Transaction, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (identity:AWSSESIdentity{id: record.arn})
    ON CREATE SET identity.firstseen = timestamp(),
        identity.arn = record.arn
    SET identity.lastupdated = $aws_update_tag,
        identity.name = record.name,
        identity.region = record.region,
        identity.consolelink = record.consolelink,
        identity.dkim_enabled = record.dkim.DkimEnabled,
        identity.dkim_verification_status = record.dkim.DkimVerificationStatus,
        identity.verification_status = record.verification.VerificationStatus
    WITH identity
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(identity)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
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

        ids = get_ses_identity(boto3_session, region)
        identities.extend(transform_identities(boto3_session, ids, region, current_aws_account_id))

    logger.info(f"Total SES Identities: {len(identities)}")

    load_ses_identity(neo4j_session, identities, current_aws_account_id, update_tag)
    cleanup_ses_identities(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process SES Service: {toc - tic:0.4f} seconds")

import logging

import boto3
import botocore.exceptions

from . import dynamodb
from . import ec2
from . import elasticsearch
from . import iam
from . import organizations
from . import rds
from . import route53
from . import s3
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def _sync_one_account(neo4j_session, boto3_session, account_id, regions, sync_tag, common_job_parameters):
    iam.sync(neo4j_session, boto3_session, account_id, sync_tag, common_job_parameters)
    s3.sync(neo4j_session, boto3_session, account_id, sync_tag, common_job_parameters)
    dynamodb.sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    rds.sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

    # NOTE each of the below will generate DNS records
    route53.sync(neo4j_session, boto3_session, account_id, sync_tag)
    elasticsearch.sync(neo4j_session, boto3_session, account_id, sync_tag)

    # NOTE clean up all DNS records, regardless of which job created them
    run_cleanup_job('aws_account_dns_cleanup.json', neo4j_session, common_job_parameters)


def _sync_multiple_accounts(neo4j_session, accounts, regions, sync_tag, common_job_parameters):
    logger.debug("Syncing AWS accounts: %s", ', '.join(accounts.values()))
    organizations.sync(neo4j_session, accounts, sync_tag, common_job_parameters)

    for profile_name, account_id in accounts.items():
        logger.info("Syncing AWS account with ID '%s' using configured profile '%s'.", account_id, profile_name)
        common_job_parameters["AWS_ID"] = account_id
        boto3_session = boto3.Session(profile_name=profile_name)

        _sync_one_account(neo4j_session, boto3_session, account_id, regions, sync_tag, common_job_parameters)

    del common_job_parameters["AWS_ID"]

    # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # up those nodes after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_principals_cleanup.json', neo4j_session, common_job_parameters)
    # There may be orphan DNS entries that point outside of known AWS zones. This job cleans
    # up those entries after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_dns_cleanup.json', neo4j_session, common_job_parameters)


def start_aws_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    try:
        boto3_session = boto3.Session()
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug("Error occurred calling boto3.Session().", exc_info=True)
        logger.error(
            (
                "Unable to initialize the default AWS session, an error occurred: %s. Make sure your AWS credentials "
                "are configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return

    if config.aws_sync_all_profiles:
        aws_accounts = organizations.get_aws_accounts_from_botocore_config(boto3_session)
    else:
        aws_accounts = organizations.get_aws_account_default(boto3_session)

    if not aws_accounts:
        logger.warning(
            "No valid AWS credentials could be found. No AWS accounts can be synced. Exiting AWS sync stage.",
        )
        return
    if len(list(aws_accounts.values())) != len(set(aws_accounts.values())):
        logger.warning(
            (
                "There are duplicate AWS accounts in your AWS configuration. It is strongly recommended that you run "
                "cartography with an AWS configuration which has exactly one profile for each AWS account you want to "
                "sync. Doing otherwise will result in undefined and untested behavior."
            ),
        )

    try:
        regions = ec2.get_ec2_regions(boto3_session)
    except botocore.exceptions.ClientError as e:
        logger.debug("Error occurred getting EC2 regions.", exc_info=True)
        logger.error(
            (
                "Failed to retrieve AWS region list, an error occurred: %s. The AWS sync cannot run without a valid "
                "region list."
            ),
            e,
        )
        return

    _sync_multiple_accounts(neo4j_session, aws_accounts, regions, config.update_tag, common_job_parameters)

    run_analysis_job(
        'aws_ec2_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

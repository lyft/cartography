import logging

import boto3
import botocore.exceptions

from cartography.intel.aws import dynamodb
from cartography.intel.aws import ec2
from cartography.intel.aws import elasticsearch
from cartography.intel.aws import iam
from cartography.intel.aws import organizations
from cartography.intel.aws import rds
from cartography.intel.aws import route53
from cartography.intel.aws import s3
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def _sync_one_account(session, boto3_session, account_id, regions, sync_tag, common_job_parameters):
    # IAM
    iam.sync(session, boto3_session, account_id, sync_tag, common_job_parameters)

    # S3
    s3.sync(session, boto3_session, account_id, sync_tag, common_job_parameters)

    # Dynamo
    dynamodb.sync_dynamodb_tables(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

    # EC2
    # TODO move this to EC2 module
    logger.info("Syncing EC2 for account '%s'.", account_id)
    ec2.sync_vpc(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync_ec2_security_groupinfo(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync_ec2_instances(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync_ec2_auto_scaling_groups(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync_load_balancers(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    ec2.sync_vpc_peering(session, boto3_session, regions, sync_tag, account_id, common_job_parameters)

    # RDS
    rds.sync_rds_instances(session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

    # NOTE each of the below will generate DNS records
    # Route53
    route53.sync_route53(session, boto3_session, account_id, sync_tag)

    # Elasticsearch
    elasticsearch.sync(session, boto3_session, account_id, sync_tag)

    # NOTE clean up all DNS records, regardless of which job created them
    run_cleanup_job('aws_account_dns_cleanup.json', session, common_job_parameters)


def _sync_multiple_accounts(session, accounts, regions, sync_tag, common_job_parameters):
    logger.debug("Syncing AWS accounts: %s", ', '.join(accounts.values()))
    organizations.sync(session, accounts, sync_tag, common_job_parameters)

    for profile_name, account_id in accounts.items():
        logger.info("Syncing AWS account with ID '%s' using configured profile '%s'.", account_id, profile_name)
        common_job_parameters["AWS_ID"] = account_id
        boto3_session = boto3.Session(profile_name=profile_name)

        _sync_one_account(session, boto3_session, account_id, regions, sync_tag, common_job_parameters)

    del common_job_parameters["AWS_ID"]

    # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # up those nodes after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_principals_cleanup.json', session, common_job_parameters)
    # There may be orphan DNS entries that point outside of known AWS zones. This job cleans
    # up those entries after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_dns_cleanup.json', session, common_job_parameters)


def start_aws_ingestion(session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    try:
        default_boto3_session = boto3.Session()
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
        aws_accounts = organizations.get_aws_accounts_from_botocore_config(default_boto3_session)
    else:
        aws_accounts = organizations.get_aws_account_default(default_boto3_session)

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
        regions = ec2.get_ec2_regions(default_boto3_session)
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

    _sync_multiple_accounts(session, aws_accounts, regions, config.update_tag, common_job_parameters)

    run_analysis_job(
        'aws_ec2_asset_exposure.json',
        session,
        common_job_parameters,
    )

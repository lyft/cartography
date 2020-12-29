import logging

import boto3
import botocore.exceptions
import neo4j

from . import dynamodb
from . import ec2
from . import ecr
from . import eks
from . import elasticsearch
from . import iam
from . import lambda_function
from . import organizations
from . import permission_relationships
from . import rds
from . import redshift
from . import resourcegroupstaggingapi
from . import route53
from . import s3
from .util import AwsStageConfig
from .util import GraphJobParameters
from cartography.config import Config
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _sync_one_account(neo4j_session: neo4j.Session, aws_stage_config: AwsStageConfig) -> None:
    try:
        regions = ec2.get_ec2_regions(aws_stage_config.boto3_session)
    except botocore.exceptions.ClientError as e:
        logger.debug("Error occurred getting EC2 regions.", exc_info=True)
        logger.error(
            (
                "Failed to retrieve AWS region list, an error occurred: %s. Could not get regions for account %s."
            ),
            e,
            aws_stage_config.current_aws_account_id,
        )
        return

    aws_stage_config.current_aws_account_regions = regions
    iam.sync(neo4j_session, aws_stage_config)
    s3.sync(neo4j_session, aws_stage_config)
    dynamodb.sync(neo4j_session, aws_stage_config)
    ec2.sync(neo4j_session, aws_stage_config)
    ecr.sync(neo4j_session, aws_stage_config)
    eks.sync(neo4j_session, aws_stage_config)
    lambda_function.sync(neo4j_session, aws_stage_config)
    rds.sync(neo4j_session, aws_stage_config)
    redshift.sync(neo4j_session, aws_stage_config)

    # NOTE each of the below will generate DNS records
    route53.sync(neo4j_session, aws_stage_config)
    elasticsearch.sync(neo4j_session, aws_stage_config)

    # NOTE clean up all DNS records, regardless of which job created them
    run_cleanup_job('aws_account_dns_cleanup.json', neo4j_session, aws_stage_config.graph_job_parameters)

    # MAP IAM permissions
    permission_relationships.sync(neo4j_session, aws_stage_config)

    # AWS Tags - Must always be last.
    resourcegroupstaggingapi.sync(neo4j_session, aws_stage_config)


def _autodiscover_accounts(neo4j_session: neo4j.Session, aws_stage_config: AwsStageConfig) -> None:
    logger.info("Trying to autodiscover accounts.")
    try:
        # Fetch all accounts
        client = aws_stage_config.boto3_session.client('organizations')
        paginator = client.get_paginator('list_accounts')
        account_list = []
        for page in paginator.paginate():
            account_list.extend(page['Accounts'])

        # Filter out every account which is not in the ACTIVE status
        # and select only the Id and Name fields
        accounts = {x['Name']: x['Id'] for x in account_list if x['Status'] == 'ACTIVE'}

        # Add them to the graph
        logger.info("Loading autodiscovered accounts.")
        organizations.load_aws_accounts(
            neo4j_session, accounts, aws_stage_config.graph_job_parameters['UPDATE_TAG'],
            aws_stage_config.graph_job_parameters,
        )
    except botocore.exceptions.ClientError:
        logger.debug(
            f"The current account ({aws_stage_config.current_aws_account_id}) doesn't have enough permissions to "
            f"perform autodiscovery.",
        )


def _sync_multiple_accounts(neo4j_session: neo4j.Session, aws_stage_config: AwsStageConfig) -> None:
    logger.debug("Syncing AWS accounts: %s", ', '.join(aws_stage_config.aws_accounts.values()))
    organizations.sync(neo4j_session, aws_stage_config)

    for profile_name, account_id in aws_stage_config.aws_accounts.items():
        logger.info("Syncing AWS account with ID '%s' using configured profile '%s'.", account_id, profile_name)
        aws_stage_config.current_aws_account_id = account_id
        aws_stage_config.graph_job_parameters["AWS_ID"] = account_id
        aws_stage_config.boto3_session = boto3.Session(profile_name=profile_name)
        _autodiscover_accounts(neo4j_session, aws_stage_config)

        _sync_one_account(neo4j_session, aws_stage_config)

    del aws_stage_config.graph_job_parameters["AWS_ID"]

    # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # up those nodes after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_principals_cleanup.json', neo4j_session, aws_stage_config.graph_job_parameters)

    # There may be orphan DNS entries that point outside of known AWS zones. This job cleans
    # up those entries after all AWS accounts have been synced.
    run_cleanup_job('aws_post_ingestion_dns_cleanup.json', neo4j_session, aws_stage_config.graph_job_parameters)


@timeit
def start_aws_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
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

    aws_stage_config = AwsStageConfig(
        boto3_session=None,
        current_aws_account_id='',
        current_aws_account_regions=[],
        graph_job_parameters=GraphJobParameters(UPDATE_TAG=config.update_tag),
        permission_relationships_file=config.permission_relationships_file,
        aws_accounts=aws_accounts,
    )

    _sync_multiple_accounts(neo4j_session, aws_stage_config)

    run_analysis_job(
        'aws_ec2_asset_exposure.json',
        neo4j_session,
        aws_stage_config.graph_job_parameters,
    )

    run_analysis_job(
        'aws_ec2_keypair_analysis.json',
        neo4j_session,
        aws_stage_config.graph_job_parameters,
    )

    run_analysis_job(
        'aws_eks_asset_exposure.json',
        neo4j_session,
        aws_stage_config.graph_job_parameters,
    )

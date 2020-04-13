import logging

import boto3
import botocore.exceptions

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_account_from_arn(arn):
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_caller_identity(boto3_session):
    client = boto3_session.client('sts')
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session):
    return get_caller_identity(boto3_session)['Account']


def get_aws_account_default(boto3_session):
    try:
        return {boto3_session.profile_name: get_current_aws_account_id(boto3_session)}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug("Error occurred getting default AWS account number.", exc_info=True)
        logger.error(
            (
                "Unable to get AWS account number, an error occurred: '%s'. Make sure your AWS credentials are "
                "configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return {}


def get_aws_accounts_from_botocore_config(boto3_session):
    d = {}
    for profile_name in boto3_session.available_profiles:
        if profile_name == 'default':
            logger.debug("Skipping AWS profile 'default'.")
            continue
        try:
            profile_boto3_session = boto3.Session(profile_name=profile_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            logger.debug("Error occurred calling boto3.Session() with profile_name '%s'.", profile_name, exc_info=True)
            logger.error(
                (
                    "Unable to initialize an AWS session using profile '%s', an error occurred: '%s'. Make sure your "
                    "AWS credentials are configured correctly, your AWS config file is valid, and your credentials "
                    "have the SecurityAudit policy attached."
                ),
                profile_name,
                e,
            )
            continue
        try:
            d[profile_name] = get_current_aws_account_id(profile_boto3_session)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            logger.debug(
                "Error occurred getting AWS account number with profile_name '%s'.",
                profile_name,
                exc_info=True,
            )
            logger.error(
                (
                    "Unable to get AWS account number using profile '%s', an error occurred: '%s'. Make sure your AWS "
                    "credentials are configured correctly, your AWS config file is valid, and your credentials have "
                    "the SecurityAudit policy attached."
                ),
                profile_name,
                e,
            )
            continue
        logger.debug(
            "Discovered AWS account '%s' associated with configured profile '%s'.",
            d[profile_name],
            profile_name,
        )
    return d


def load_aws_accounts(neo4j_session, aws_accounts, aws_update_tag, common_job_parameters):
    query = """
    MERGE (aa:AWSAccount{id: {ACCOUNT_ID}})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = {aws_update_tag}, aa.name = {ACCOUNT_NAME}
    WITH aa
    MERGE (root:AWSPrincipal{arn: {RootArn}})
    ON CREATE SET root.firstseen = timestamp(), root.type = 'AWS'
    SET root.lastupdated = {aws_update_tag}
    WITH aa, root
    MERGE (aa)-[r:RESOURCE]->(root)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag};
    """
    for account_name, account_id in aws_accounts.items():
        root_arn = f'arn:aws:iam::{account_id}:root'
        neo4j_session.run(
            query,
            ACCOUNT_ID=account_id,
            ACCOUNT_NAME=account_name,
            RootArn=root_arn,
            aws_update_tag=aws_update_tag,
        )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, accounts, aws_update_tag, common_job_parameters):
    load_aws_accounts(neo4j_session, accounts, aws_update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

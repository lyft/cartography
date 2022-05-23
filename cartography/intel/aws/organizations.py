import logging
from typing import Dict
from typing import List
from typing import Optional

import boto3
import botocore.exceptions
import neo4j

from cartography.util import timeit
from cartography.util import get_stats_client
from cartography.util import merge_module_sync_metadata

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def get_account_from_arn(arn: str) -> str:
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_caller_identity(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('sts')
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session: boto3.session.Session) -> Dict:
    return get_caller_identity(boto3_session)['Account']


def get_aws_account_default(boto3_session: boto3.session.Session) -> Dict:
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


def get_aws_accounts_from_botocore_config(boto3_session: boto3.session.Session) -> Dict:
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


def describe_organization(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("organizations")
    return client.describe_organization()


def get_current_organization(boto3_session: boto3.session.Session) -> Dict:
    return describe_organization(boto3_session)["Organization"]


def autodiscovery_accounts(
    boto3_session: boto3.session.Session,
) -> List[Dict]:
    # Fetch all accounts
    client = boto3_session.client("organizations")
    paginator = client.get_paginator('list_accounts')
    accounts: List[Dict] = []
    for page in paginator.paginate():
        accounts.extend(page['Accounts'])

    # Filter out every account which is not in the ACTIVE status
    # and select only the Id and Name fields
    filtered_accounts: List[Dict] = [x for x in accounts if x['Status'] == 'ACTIVE']
    return filtered_accounts


def load_aws_organization(
    neo4j_session: neo4j.Session,
    organization: Dict,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading AWS Organization {organization['Id']}")
    query = """
    WITH {Organization} AS organization
    MERGE (ao:AWSOrganization{id: organization.Id})
    ON CREATE SET ao.firstseen = timestamp()
    SET ao.lastupdated = {aws_update_tag},
    ao.arn = organization.Arn,
    ao.feature_set = organization.FeatureSet,
    ao.master_account_arn = organization.MasterAccountArn,
    ao.master_account_id = organization.MasterAccountId,
    ao.master_account_email = organization.MasterAccountEmail
    """
    neo4j_session.run(
        query,
        Organization=organization,
        aws_update_tag=aws_update_tag,
    )


def load_aws_accounts(
    neo4j_session: neo4j.Session, aws_accounts: Dict, aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
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


def load_autodiscovery_aws_accounts(
    neo4j_session: neo4j.Session,
    organization_id: Optional[str],
    accounts: List[Dict],
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(accounts)} Organization's accounts")
    ingest_accounts = """
    UNWIND {Accounts} AS account
        MERGE (aa:AWSAccount{id: account.Id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = {aws_update_tag},
            aa.name = account.Name,
            aa.arn = account.Arn,
            aa.email = account.Email,
            aa.status = account.Status,
            aa.joined_method = account.JoinedMethod,
            aa.joined_timestamp = account.JoinedTimestamp
        WITH aa
        MERGE (root:AWSPrincipal{arn: 'arn:aws:iam::'+aa.id+':root'})
        ON CREATE SET root.firstseen = timestamp(), root.type = 'AWS'
        SET root.lastupdated = {aws_update_tag}
        WITH aa, root
        MERGE (aa)-[r:RESOURCE]->(root)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        WITH aa
        MATCH (ao:AWSOrganization{id: {OrganizationId}})
        WITH aa, ao
        MERGE (aa)-[r:BELONG_TO]->(ao)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_accounts,
        Accounts=accounts,
        OrganizationId=organization_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def sync_autodiscovery(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    account_id: str,
    update_tag: int,
) -> None:
    try:
        logger.info("Loading autodiscovered organization and accounts.")
        organization = get_current_organization(boto3_session)
        accounts = autodiscovery_accounts(boto3_session)
        organization_id = organization["Id"]
        load_aws_organization(neo4j_session, organization, update_tag)
        load_autodiscovery_aws_accounts(neo4j_session, organization_id, accounts, update_tag)
        merge_module_sync_metadata(
            neo4j_session,
            group_type="AWSAccount",
            group_id=organization_id,
            synced_type="AWSOrganization",
            update_tag=update_tag,
            stat_handler=stat_handler,
        )

    except botocore.exceptions.ClientError:
            logger.warning(f"The current account ({account_id}) doesn't have enough permissions to perform autodiscovery.")


@timeit
def sync(neo4j_session: neo4j.Session, accounts: Dict, update_tag: int, common_job_parameters: Dict) -> None:
    load_aws_accounts(neo4j_session, accounts, update_tag, common_job_parameters)

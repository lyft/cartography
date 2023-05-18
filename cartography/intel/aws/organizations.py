import logging
import uuid
from typing import Dict
from typing import Optional
from typing import List

import boto3
import botocore.exceptions
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
import neo4j
from cartography.util import timeit

logger = logging.getLogger(__name__)


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

@timeit
def get_account_public_access_block(account_id: str, boto3_session: boto3.session.Session) -> Optional[Dict]:
    """
    Gets the S3 bucket public access block configuration.
    """
    client = boto3_session.client('s3control')
    public_access_block = None
    try:
        public_access_block = client.get_public_access_block(AccountId=account_id)
    except ClientError as e:
        logger.info("Error in getting Account Level Public Access Block for '%s', Error: '%s'", 
        account_id,
        e.args[0])
        pass
    except EndpointConnectionError:
        logger.warning(
            f"Failed to retrieve S3 account public access block for account")
    return public_access_block

@timeit
def parse_account_public_access_block(account_id: str,public_access_block: Optional[Dict]) -> Optional[Dict]:
    """ Parses the account level public access block object and returns a dict of the relevant data """
    # Public Access Block configuration object JSON looks like:
    # {
    #     'PublicAccessBlockConfiguration': {
    #         'BlockPublicAcls': True|False,
    #         'IgnorePublicAcls': True|False,
    #         'BlockPublicPolicy': True|False,
    #         'RestrictPublicBuckets': True|False
    #     }
    # }
    if public_access_block is None:
        return None
    pab = public_access_block["PublicAccessBlockConfiguration"]
    return {
        "account_id": account_id,
        "block_public_acls": pab.get("BlockPublicAcls"),
        "ignore_public_acls": pab.get("IgnorePublicAcls"),
        "block_public_policy": pab.get("BlockPublicPolicy"),
        "restrict_public_buckets": pab.get("RestrictPublicBuckets"),
    }

@timeit
def _load_account_public_access_block(
    neo4j_session: neo4j.Session,
    account_public_access_block_configs: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest S3 public access block results into neo4j.
    """
    ingest_account_public_access_block = """
    UNWIND {account_public_access_block_configs} AS account_public_access_block
    MATCH (s:AWSAccount) where s.id = account_public_access_block.account_id
    SET s.account_block_public_acls = account_public_access_block.block_public_acls,
        s.account_ignore_public_acls = account_public_access_block.ignore_public_acls,
        s.account_block_public_policy = account_public_access_block.block_public_policy,
        s.account_restrict_public_buckets = account_public_access_block.restrict_public_buckets,
        s.lastupdated = {UpdateTag}
    """

    neo4j_session.run(
        ingest_account_public_access_block,
        account_public_access_block_configs=account_public_access_block_configs,
        UpdateTag=update_tag,
    )


def load_aws_accounts(
    neo4j_session: neo4j.Session, aws_accounts: Dict, aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    query = """
    MERGE (aa:AWSAccount{id: $ACCOUNT_ID})
    ON CREATE SET aa.firstseen = timestamp(),
    aa.borneo_id = {account_borneo_id}
    SET aa.lastupdated = $aws_update_tag, aa.name = $ACCOUNT_NAME, aa.inscope=true
    REMOVE aa.foreign
    WITH aa
    MERGE (root:AWSPrincipal{arn: {RootArn}})
    ON CREATE SET root.firstseen = timestamp(), root.type = 'AWS',
    root.borneo_id = apoc.create.uuid()
    SET root.lastupdated = {aws_update_tag}
    WITH aa, root
    MERGE (aa)-[r:RESOURCE]->(root)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag;
    """
    for account_name, account_id in aws_accounts.items():
        root_arn = f'arn:aws:iam::{account_id}:root'
        neo4j_session.run(
            query,
            ACCOUNT_ID=account_id,
            ACCOUNT_NAME=account_name,
            RootArn=root_arn,
            aws_update_tag=aws_update_tag
        )

def load_accounts_public_access_block(
  neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, account_id: str, aws_update_tag: int
) -> None:
  account_public_access_block = get_account_public_access_block(account_id, boto3_session)
  account_public_access_block_configs: List[Dict] = []
  parsed_account_public_access_block = parse_account_public_access_block(account_id,account_public_access_block)
  logger.debug(parsed_account_public_access_block)
  if parsed_account_public_access_block is not None:
    account_public_access_block_configs.append(parsed_account_public_access_block)
  _load_account_public_access_block(neo4j_session, account_public_access_block_configs, aws_update_tag)
  
@timeit
def sync(neo4j_session: neo4j.Session, accounts: Dict, update_tag: int, common_job_parameters: Dict) -> None:
    load_aws_accounts(neo4j_session, accounts, update_tag, common_job_parameters)

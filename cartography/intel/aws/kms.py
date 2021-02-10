import json
import logging

from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_kms_key_list(boto3_session, region):
    client = boto3_session.client('kms', region_name=region)
    paginator = client.get_paginator('list_keys')
    key_list = []
    for page in paginator.paginate():
        key_list.extend(page['Keys'])

    described_key_list = []
    for key in key_list:
        try:
            response = client.describe_key(KeyId=key["KeyId"])['KeyMetadata']
        except ClientError as e:
            logger.warning("Failed to describe key with key id - {}. Error - {}".format(key["KeyId"], e))
            raise

        described_key_list.append(response)

    return described_key_list


@timeit
@aws_handle_regions
def get_kms_key_details(boto3_session, kms_key_data, region):
    """
    Iterates over all KMS Keys.
    """
    client = boto3_session.client('kms', region_name=region)
    for key in kms_key_data:
        policy = get_policy(key, client)
        aliases = get_aliases(key, client)
        grants = get_grants(key, client)
        yield key['KeyId'], policy, aliases, grants


@timeit
def get_policy(key, client):
    """
    Gets the KMS Key policy. Returns policy string or None if no policy
    """
    try:
        policy = client.get_key_policy(KeyId=key["KeyId"], PolicyName='default')
    except ClientError as e:
        policy = None
        logger.warning("Failed to retrieve Key Policy for key id - {}. Error - {}".format(key["KeyId"], e))
        raise

    return policy


@timeit
def get_aliases(key, client):
    """
    Gets the KMS Key Aliases.
    """
    aliases = []
    paginator = client.get_paginator('list_aliases')
    for page in paginator.paginate(KeyId=key['KeyId']):
        aliases.extend(page['Aliases'])

    return aliases


@timeit
def get_grants(key, client):
    """
    Gets the KMS Key Grants.
    """
    grants = []
    paginator = client.get_paginator('list_grants')
    for page in paginator.paginate(KeyId=key['KeyId']):
        grants.extend(page['Grants'])

    return grants


@timeit
def _load_kms_key_aliases(neo4j_session, aliases, update_tag):
    """
    Ingest KMS Aliases into neo4j.
    """
    ingest_aliases = """
    MERGE (a:KMSAlias{id: {AliasArn}})
    ON CREATE SET a.firstseen = timestamp(), a.targetkeyid = {TargetKeyId}
    SET a.aliasname = {AliasName}, a.lastupdated = {UpdateTag}
    WITH a MATCH (kmskey:KMSKey{id: {TargetKeyId}})
    MERGE (a)-[r:KNOWN_AS]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for alias in aliases:
        neo4j_session.run(
            ingest_aliases,
            AliasArn=alias["AliasArn"],
            AliasName=alias.get("AliasName"),
            TargetKeyId=alias["TargetKeyId"],
            UpdateTag=update_tag,
        )


@timeit
def _load_kms_key_grants(neo4j_session, grants_list, update_tag):
    """
    Ingest KMS Key Grants into neo4j.
    """
    ingest_grants = """
    MERGE (g:KMSGrant{id: {GrantId}})
    ON CREATE SET g.firstseen = timestamp(), g.granteeprincipal = {GranteePrincipal}, g.creationdate = {CreationDate}
    SET g.name = {GrantName}, g.lastupdated = {UpdateTag}
    WITH g
    MATCH (kmskey:KMSKey{id: {TargetKeyId}})
    MERGE (g)-[r:APPLIED_ON]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for grant in grants_list:
        neo4j_session.run(
            ingest_grants,
            GrantId=grant["GrantId"],
            GrantName=grant.get("Name"),
            GranteePrincipal=grant.get("GranteePrincipal"),
            CreationDate=grant["CreationDate"],
            TargetKeyId=grant["KeyId"],
            UpdateTag=update_tag,
        )


@timeit
def _load_kms_key_policies(neo4j_session, policies, update_tag):
    """
    Ingest KMS Key policy results into neo4j.
    """
    # NOTE we use the coalesce function so appending works when the value is null initially
    ingest_policies = """
    UNWIND {policies} AS policy
    MATCH (k:KMSKey) where k.name = policy.kms_key
    SET k.anonymous_access = (coalesce(k.anonymous_access, false) OR policy.internet_accessible),
    k.anonymous_actions = coalesce(k.anonymous_actions, []) + policy.accessible_actions,
    k.lastupdated = {UpdateTag}
    """

    neo4j_session.run(
        ingest_policies,
        policies=policies,
        UpdateTag=update_tag,
    )


def _set_default_values(neo4j_session, aws_account_id):
    set_defaults = """
    MATCH (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(kmskey:KMSKey) where NOT EXISTS(kmskey.anonymous_actions)
    SET kmskey.anonymous_access = false, kmskey.anonymous_actions = []
    """

    neo4j_session.run(
        set_defaults,
        AWS_ID=aws_account_id,
    )


@timeit
def load_kms_key_details(neo4j_session, policy_alias_grants_data, region, aws_account_id, update_tag):
    """
    Create dictionaries for all KMS key policies, aliases and grants so we can import them in a single query for each
    """
    policies = []
    aliases = []
    grants = []
    for key, policy, alias, grant in policy_alias_grants_data:
        parsed_policy = parse_policy(key, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)
        if len(alias) > 0:
            aliases.extend(alias)
        if len(grants) > 0:
            grants.extend(grant)

    # cleanup existing policy properties
    run_cleanup_job(
        'aws_kms_details.json',
        neo4j_session,
        {'UPDATE_TAG': update_tag, 'AWS_ID': aws_account_id},
    )

    _load_kms_key_policies(neo4j_session, policies, update_tag)
    _load_kms_key_aliases(neo4j_session, aliases, update_tag)
    _load_kms_key_grants(neo4j_session, grants, update_tag)
    _set_default_values(neo4j_session, aws_account_id)


@timeit
def parse_policy(key, policy):
    """
    Uses PolicyUniverse to parse S3 policies and returns the internet accessibility results
    """
    # policy is not required, so may be None
    # policy JSON format. Note condition can be any JSON statement so will need to import as-is
    # policy is a very complex format, so the policyuniverse library will be used for parsing out important data
    # ...metadata...
    # "Policy" :
    # {
    #   "Version": "2012-10-17",
    #   "Id": "key-consolepolicy-5",
    #   "Statement": [
    #     {
    #       "Sid": "Enable IAM User Permissions",
    #       "Effect": "Allow",
    #       "Principal": {
    #         "AWS": "arn:aws:iam::123456789012:root"
    #       },
    #       "Action": "kms:*",
    #       "Resource": "*"
    #     },
    #     {
    #       "Sid": "Allow access for Key Administrators",
    #       "Effect": "Allow",
    #       "Principal": {
    #         "AWS": "arn:aws:iam::123456789012:role/ec2-manager"
    #       },
    #       "Action": [
    #         "kms:Create*",
    #         "kms:Describe*",
    #         "kms:Enable*",
    #         "kms:List*",
    #         "kms:Put*",
    #         "kms:Update*",
    #         "kms:Revoke*",
    #         "kms:Disable*",
    #         "kms:Get*",
    #         "kms:Delete*",
    #         "kms:ScheduleKeyDeletion",
    #         "kms:CancelKeyDeletion"
    #       ],
    #       "Resource": "*"
    #     }
    #   ]
    # }
    if policy is not None:
        # get just the policy element and convert to JSON because boto3 returns this as string
        policy = Policy(json.loads(policy['Policy']))
        if policy.is_internet_accessible():
            return {
                "kms_key": key,
                "internet_accessible": True,
                "accessible_actions": list(policy.internet_accessible_actions()),
            }
        else:
            return None
    else:
        return None


@timeit
def load_kms_keys(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_keys = """
    MERGE (kmskey:KMSKey{id:{KeyId}})
    ON CREATE SET kmskey.firstseen = timestamp(),
    kmskey.arn = {Arn}, kmskey.creationdate = {CreationDate}
    SET kmskey.deletiondate = {DeletionDate},
    kmskey.validto = {ValidTo},
    kmskey.enabled = {Enabled},
    kmskey.keystate = {KeyState},
    kmskey.customkeystoreid = {CustomKeyStoreId},
    kmskey.cloudhsmclusterid = {CloudHsmClusterId},
    kmskey.lastupdated = {aws_update_tag},
    kmskey.region = {Region}
    WITH kmskey
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    # The owner data returned by the API maps to the aws account nickname and not the IAM user
    # there doesn't seem to be a way to retreive the mapping but we can get the current context account
    # so we map to that directly

    for kms_key in data:
        neo4j_session.run(
            ingest_keys,
            KeyId=kms_key["KeyId"],
            Arn=kms_key["Arn"],
            CreationDate=str(kms_key["CreationDate"]),
            DeletionDate=str(kms_key.get("DeletionDate")),
            ValidTo=str(kms_key.get("ValidTo")),
            Enabled=kms_key["Enabled"],
            KeyState=kms_key["KeyState"],
            CustomKeyStoreId=kms_key.get("CustomKeyStoreId"),
            CloudHsmClusterId=kms_key.get("CloudHsmClusterId"),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_kms(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_kms_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_kms_keys(neo4j_session, boto3_session, region, current_aws_account_id, aws_update_tag):
    kms_keys = get_kms_key_list(boto3_session, region)

    load_kms_keys(neo4j_session, kms_keys, region, current_aws_account_id, aws_update_tag)

    policy_alias_grants_data = get_kms_key_details(boto3_session, kms_keys, region)
    load_kms_key_details(neo4j_session, policy_alias_grants_data, region, current_aws_account_id, aws_update_tag)


@timeit
def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.info("Inside KMS")
    for region in regions:
        logger.info("Syncing KMS for region %s in account '%s'.", region, current_aws_account_id)
        sync_kms_keys(neo4j_session, boto3_session, region, current_aws_account_id, aws_update_tag)

    cleanup_kms(neo4j_session, common_job_parameters)

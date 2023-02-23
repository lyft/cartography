import csv
import enum
import io
import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import dateutil.parser as dp
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.aws.permission_relationships import parse_statement_node
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.stats import get_stats_client
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = 'managed'
    inline = 'inline'


@timeit
def get_group_policies(boto3_session: boto3.session.Session, group_name: str) -> Dict:
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_group_policies')
    policy_names: List[Dict] = []
    for page in paginator.paginate(GroupName=group_name):
        policy_names.extend(page['PolicyNames'])
    return {'PolicyNames': policy_names}


@timeit
def get_group_policy_info(
        boto3_session: boto3.session.Session, group_name: str, policy_name: str,
) -> Any:
    client = boto3_session.client('iam')
    return client.get_group_policy(GroupName=group_name, PolicyName=policy_name)


@timeit
def get_group_membership_data(boto3_session: boto3.session.Session, group_name: str) -> Dict:
    client = boto3_session.client('iam')
    try:
        memberships = client.get_group(GroupName=group_name)
        return memberships
    except client.exceptions.NoSuchEntityException:
        # Avoid crashing the sync
        logger.warning("client.get_group(GroupName='%s') failed with NoSuchEntityException; skipping.", group_name)
        return {}


@timeit
def get_group_policy_data(boto3_session: boto3.session.Session, group_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[arn] = policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_group.policies.all()}
    return policies


@timeit
def get_group_managed_policy_data(boto3_session: boto3.session.Session, group_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[arn] = {
            p.policy_name: p.default_version.document["Statement"]
            for p in resource_group.attached_policies.all()
        }
    return policies


@timeit
def get_user_policy_data(boto3_session: boto3.session.Session, user_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for user in user_list:
        name = user["UserName"]
        arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_user.policies.all()}
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_user_managed_policy_data(boto3_session: boto3.session.Session, user_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for user in user_list:
        name = user["UserName"]
        arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[arn] = {
                p.policy_name: p.default_version.document["Statement"]
                for p in resource_user.attached_policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_role_policy_data(boto3_session: boto3.session.Session, role_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_role.policies.all()}
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_role_managed_policy_data(boto3_session: boto3.session.Session, role_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource('iam')
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[arn] = {
                p.policy_name: p.default_version.document["Statement"]
                for p in resource_role.attached_policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_user_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('iam')

    paginator = client.get_paginator('list_users')
    users: List[Dict] = []
    for page in paginator.paginate():
        users.extend(page['Users'])
    return {'Users': users}


@timeit
def get_group_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_groups')
    groups: List[Dict] = []
    for page in paginator.paginate():
        groups.extend(page['Groups'])
    return {'Groups': groups}


@timeit
def get_role_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_roles')
    roles: List[Dict] = []
    for page in paginator.paginate():
        roles.extend(page['Roles'])
    return {'Roles': roles}


@timeit
def get_account_access_key_data(boto3_session: boto3.session.Session, username: str) -> Dict:
    client = boto3_session.client('iam')
    # NOTE we can get away without using a paginator here because users are limited to two access keys
    access_keys: Dict = {}
    try:
        access_keys = client.list_access_keys(UserName=username)
    except client.exceptions.NoSuchEntityException:
        logger.warning(
            f"Could not get access key for user {username} due to NoSuchEntityException; skipping.",
        )
    return access_keys


@timeit
def get_server_certificates(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_server_certificates')
    server_certificates: List[Dict] = []
    for page in paginator.paginate():
        server_certificates.extend(page['ServerCertificateMetadataList'])
    return server_certificates


def _attempt_get_credential_report_content(boto3_session: boto3.session.Session) -> Optional[bytes]:
    client = boto3_session.client('iam')
    try:
        return client.get_credential_report()['Content']
    except (
        client.exceptions.CredentialReportNotPresentException,
        client.exceptions.CredentialReportExpiredException,
        client.exceptions.CredentialReportNotReadyException,
    ):
        return None


def _attempt_generate_credential_report_content(boto3_session: boto3.session.Session) -> None:
    client = boto3_session.client('iam')
    client.generate_credential_report()


@timeit
def get_credential_report_content(boto3_session: boto3.session.Session) -> Optional[bytes]:
    content = None
    for _ in range(3):
        content = _attempt_get_credential_report_content(boto3_session)
        if content is None:
            _attempt_generate_credential_report_content(boto3_session)
        else:
            return content
        time.sleep(3)
    return content


def transform_credential_report_users(credential_report_content: Optional[bytes]) -> List:
    def str_to_optional_bool(s: str) -> Optional[bool]:
        return True if s == 'true' else False if s == 'false' else None

    def str_to_optional_timestamp(s: str) -> Optional[int]:
        try:
            return int(dp.parse(s).timestamp())
        except dp.ParserError:
            return None

    def str_to_optional_str(s: str) -> Optional[str]:
        return None if s == 'N/A' else s

    if credential_report_content is None:
        return []
    credential_report_users = []
    content_csv = credential_report_content.decode('utf-8')
    with io.StringIO(content_csv) as fp:
        csv_reader = csv.reader(fp, delimiter=",")
        next(csv_reader)
        for row in csv_reader:
            credential_report_user: Dict[str, Any] = {}
            credential_report_user['user'] = row[0]
            credential_report_user['arn'] = row[1]
            credential_report_user['user_creation_time'] = str_to_optional_timestamp(row[2])
            credential_report_user['password_enabled'] = str_to_optional_bool(row[3])
            credential_report_user['password_last_used'] = str_to_optional_timestamp(row[4])
            credential_report_user['password_last_changed'] = str_to_optional_timestamp(row[5])
            credential_report_user['password_next_rotation'] = str_to_optional_timestamp(row[6])
            credential_report_user['mfa_active'] = str_to_optional_bool(row[7])
            credential_report_user['access_key_1_active'] = str_to_optional_bool(row[8])
            credential_report_user['access_key_1_last_rotated'] = str_to_optional_timestamp(row[9])
            credential_report_user['access_key_1_last_used_date'] = str_to_optional_timestamp(row[10])
            credential_report_user['access_key_1_last_used_region'] = str_to_optional_str(row[11])
            credential_report_user['access_key_1_last_used_service'] = str_to_optional_str(row[12])
            credential_report_user['access_key_2_active'] = str_to_optional_bool(row[13])
            credential_report_user['access_key_2_last_rotated'] = str_to_optional_timestamp(row[14])
            credential_report_user['access_key_2_last_used_date'] = str_to_optional_timestamp(row[15])
            credential_report_user['access_key_2_last_used_region'] = str_to_optional_str(row[16])
            credential_report_user['access_key_2_last_used_service'] = str_to_optional_str(row[17])
            credential_report_user['cert_1_active'] = str_to_optional_bool(row[18])
            credential_report_user['cert_1_last_rotated'] = str_to_optional_timestamp(row[19])
            credential_report_user['cert_2_active'] = str_to_optional_bool(row[20])
            credential_report_user['cert_2_last_rotated'] = str_to_optional_timestamp(row[21])
            credential_report_users.append(credential_report_user)
    return credential_report_users


@timeit
def get_account_password_policy(
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
) -> Dict:
    client = boto3_session.client('iam')
    account_password_policy: Dict = {}
    try:
        account_password_policy = client.get_account_password_policy()['PasswordPolicy']
    except client.exceptions.NoSuchEntityException:
        logger.warning(
            f"Could not get account password policy for account {current_aws_account_id} "
            f"due to NoSuchEntityException; skipping.",
        )
    return account_password_policy


@timeit
def get_instance_profiles(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_instance_profiles')
    instance_profiles: List[Dict] = []
    for page in paginator.paginate():
        instance_profiles.extend(page['InstanceProfiles'])
    return {'InstanceProfiles': instance_profiles}


@timeit
def load_users(
    neo4j_session: neo4j.Session, users: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_user = """
    MERGE (unode:AWSUser{arn: $ARN})
    ON CREATE SET unode:AWSPrincipal, unode.userid = $USERID, unode.firstseen = timestamp(),
    unode.createdate = $CREATE_DATE
    SET unode.name = $USERNAME, unode.path = $PATH, unode.passwordlastused = $PASSWORD_LASTUSED,
    unode.lastupdated = $aws_update_tag
    WITH unode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(unode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    logger.info(f"Loading {len(users)} IAM users.")
    for user in users:
        neo4j_session.run(
            ingest_user,
            ARN=user["Arn"],
            USERID=user["UserId"],
            CREATE_DATE=str(user["CreateDate"]),
            USERNAME=user["UserName"],
            PATH=user["Path"],
            PASSWORD_LASTUSED=str(user.get("PasswordLastUsed", "")),
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_groups(
    neo4j_session: neo4j.Session, groups: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_group = """
    MERGE (gnode:AWSGroup{arn: $ARN})
    ON CREATE SET gnode.groupid = $GROUP_ID, gnode.firstseen = timestamp(), gnode.createdate = $CREATE_DATE
    SET gnode:AWSPrincipal, gnode.name = $GROUP_NAME, gnode.path = $PATH,gnode.lastupdated = $aws_update_tag
    WITH gnode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(gnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    logger.info(f"Loading {len(groups)} IAM groups to the graph.")
    for group in groups:
        neo4j_session.run(
            ingest_group,
            ARN=group["Arn"],
            GROUP_ID=group["GroupId"],
            CREATE_DATE=str(group["CreateDate"]),
            GROUP_NAME=group["GroupName"],
            PATH=group["Path"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


def _parse_principal_entries(principal: Dict) -> List[Tuple[Any, Any]]:
    """
    Returns a list of tuples of the form (principal_type, principal_value)
    e.g. [('AWS', 'example-role-name'), ('Service', 'example-service')]
    """
    principal_entries = []
    for principal_type in principal:
        principal_values = principal[principal_type]
        if not isinstance(principal_values, list):
            principal_values = [principal_values]
        for principal_value in principal_values:
            principal_entries.append((principal_type, principal_value))
    return principal_entries


@timeit
def load_roles(
    neo4j_session: neo4j.Session, roles: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_role = """
    MERGE (rnode:AWSPrincipal{arn: $Arn})
    ON CREATE SET rnode.roleid = $RoleId, rnode.firstseen = timestamp(),
    rnode.createdate = $CreateDate
    ON MATCH SET rnode.name = $RoleName, rnode.path = $Path
    SET rnode:AWSRole,
    rnode.lastupdated = $aws_update_tag
    WITH rnode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(rnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    ingest_policy_statement = """
    MERGE (spnnode:AWSPrincipal{arn: $SpnArn})
    ON CREATE SET spnnode.firstseen = timestamp()
    SET spnnode.lastupdated = $aws_update_tag, spnnode.type = $SpnType
    WITH spnnode
    MATCH (role:AWSRole{arn: $RoleArn})
    MERGE (role)-[r:TRUSTS_AWS_PRINCIPAL]->(spnnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    # Note - why we don't set inscope or foreign attribute on the account
    #
    # we are agnostic here if this is the AWSAccount is part of the sync scope or
    # a foreign AWS account that contains a trusted principal. The account could also be inscope
    # but not sync yet.
    # - The inscope attribute - set when the account is being sync.
    # - The foreign attribute - the attribute assignment logic is in aws_foreign_accounts.json analysis job
    # - Why seperate statement is needed - the arn may point to service level principals ex - ec2.amazonaws.com
    ingest_spnmap_statement = """
    MERGE (aa:AWSAccount{id: $SpnAccountId})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $aws_update_tag
    WITH aa
    MATCH (spnnode:AWSPrincipal{arn: $SpnArn})
    WITH spnnode, aa
    MERGE (aa)-[r:RESOURCE]->(spnnode)
    ON CREATE SET r.firstseen = timestamp()
    """

    # TODO support conditions
    logger.info(f"Loading {len(roles)} IAM roles to the graph.")
    for role in roles:
        neo4j_session.run(
            ingest_role,
            Arn=role["Arn"],
            RoleId=role["RoleId"],
            CreateDate=str(role["CreateDate"]),
            RoleName=role["RoleName"],
            Path=role["Path"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        for statement in role["AssumeRolePolicyDocument"]["Statement"]:
            principal_entries = _parse_principal_entries(statement["Principal"])
            for principal_type, principal_value in principal_entries:
                neo4j_session.run(
                    ingest_policy_statement,
                    SpnArn=principal_value,
                    SpnType=principal_type,
                    RoleArn=role['Arn'],
                    aws_update_tag=aws_update_tag,
                )
                spn_arn = get_account_from_arn(principal_value)
                if spn_arn:
                    neo4j_session.run(
                        ingest_spnmap_statement,
                        SpnArn=principal_value,
                        SpnAccountId=get_account_from_arn(principal_value),
                        aws_update_tag=aws_update_tag,
                    )


@timeit
def load_group_memberships(neo4j_session: neo4j.Session, group_memberships: Dict, aws_update_tag: int) -> None:
    ingest_membership = """
    MATCH (group:AWSGroup{arn: $GroupArn})
    WITH group
    MATCH (user:AWSUser{arn: $PrincipalArn})
    MERGE (user)-[r:MEMBER_AWS_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    WITH user, group
    MATCH (group)-[:POLICY]->(policy:AWSPolicy)
    MERGE (user)-[r2:POLICY]->(policy)
    SET r2.lastupdated = $aws_update_tag
    """

    for group_arn, membership_data in group_memberships.items():
        for info in membership_data.get("Users", []):
            principal_arn = info["Arn"]
            neo4j_session.run(
                ingest_membership,
                GroupArn=group_arn,
                PrincipalArn=principal_arn,
                aws_update_tag=aws_update_tag,
            )


@timeit
def get_policies_for_principal(neo4j_session: neo4j.Session, principal_arn: str) -> Dict:
    get_policy_query = """
    MATCH
    (principal:AWSPrincipal{arn:$Arn})-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT policy.id AS policy_id,
    COLLECT(DISTINCT statements) AS statements
    """
    results = neo4j_session.run(
        get_policy_query,
        Arn=principal_arn,
    )
    policies = {r["policy_id"]: parse_statement_node(r["statements"]) for r in results}
    return policies


@timeit
def sync_assumerole_relationships(
    neo4j_session: neo4j.Session, current_aws_account_id: str, aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    # Must be called after load_role
    # Computes and syncs the STS_ASSUME_ROLE_ALLOW allow relationship
    logger.info("Syncing assume role mappings for account '%s'.", current_aws_account_id)
    query_potential_matches = """
    MATCH (:AWSAccount{id:$AccountId})-[:RESOURCE]->(target:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(source:AWSPrincipal)
    WHERE NOT source.arn ENDS WITH 'root'
    AND NOT source.type = 'Service'
    AND NOT source.type = 'Federated'
    RETURN target.arn AS target_arn,
    source.arn AS source_arn
    """

    ingest_policies_assume_role = """
    MATCH (source:AWSPrincipal{arn: $SourceArn})
    WITH source
    MATCH (role:AWSRole{arn: $TargetArn})
    WITH role, source
    MERGE (source)-[r:STS_ASSUME_ROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    results = neo4j_session.run(
        query_potential_matches,
        AccountId=current_aws_account_id,
    )
    potential_matches = [(r["source_arn"], r["target_arn"]) for r in results]
    for source_arn, target_arn in potential_matches:
        policies = get_policies_for_principal(neo4j_session, source_arn)
        if principal_allowed_on_resource(policies, target_arn, [{"permission": "sts:AssumeRole"}]):
            neo4j_session.run(
                ingest_policies_assume_role,
                SourceArn=source_arn,
                TargetArn=target_arn,
                aws_update_tag=aws_update_tag,
            )
    run_cleanup_job(
        'aws_import_roles_policy_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def load_user_access_keys(neo4j_session: neo4j.Session, user_access_keys: Dict, aws_update_tag: int) -> None:
    # TODO change the node label to reflect that this is a user access key, not an account access key
    ingest_account_key = """
    MATCH (user:AWSUser{arn: $UserARN})
    WITH user
    MERGE (key:AccountAccessKey{accesskeyid: $AccessKeyId})
    ON CREATE SET key.firstseen = timestamp(), key.createdate = $CreateDate
    SET key.status = $Status, key.lastupdated = $aws_update_tag
    WITH user,key
    MERGE (user)-[r:AWS_ACCESS_KEY]->(key)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    for arn, access_keys in user_access_keys.items():
        for key in access_keys["AccessKeyMetadata"]:
            if key.get('AccessKeyId'):
                neo4j_session.run(
                    ingest_account_key,
                    UserARN=arn,
                    AccessKeyId=key['AccessKeyId'],
                    CreateDate=str(key['CreateDate']),
                    Status=key['Status'],
                    aws_update_tag=aws_update_tag,
                )


def ensure_list(obj: Any) -> List[Any]:
    if not isinstance(obj, list):
        obj = [obj]
    return obj


def _transform_policy_statements(statements: Any, policy_id: str) -> List[Dict]:
    count = 1
    if not isinstance(statements, list):
        statements = [statements]
    for stmt in statements:
        if "Sid" not in stmt:
            statement_id = count
            count += 1
        else:
            statement_id = stmt["Sid"]
        stmt["id"] = f"{policy_id}/statement/{statement_id}"
        if "Resource" in stmt:
            stmt["Resource"] = ensure_list(stmt["Resource"])
        if "Action" in stmt:
            stmt["Action"] = ensure_list(stmt["Action"])
        if "NotAction" in stmt:
            stmt["NotAction"] = ensure_list(stmt["NotAction"])
        if "NotResource" in stmt:
            stmt["NotResource"] = ensure_list(stmt["NotResource"])
        if "Condition" in stmt:
            stmt["Condition"] = json.dumps(ensure_list(stmt["Condition"]))
    return statements


def transform_policy_data(policy_map: Dict, policy_type: str) -> None:
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM {policy_type} policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            policy_id = transform_policy_id(principal_arn, policy_type, policy_name)
            statements = _transform_policy_statements(
                statements, policy_id,
            )


def transform_policy_id(principal_arn: str, policy_type: str, name: str) -> str:
    return f"{principal_arn}/{policy_type}_policy/{name}"


def _load_policy_tx(
    tx: neo4j.Transaction, policy_id: str, policy_name: str, policy_type: str, principal_arn: str,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_policy = """
    MERGE (policy:AWSPolicy{id: $PolicyId})
    ON CREATE SET
        policy.firstseen = timestamp(),
        policy.type = $PolicyType,
        policy.name = $PolicyName
    SET policy.lastupdated = $aws_update_tag
    WITH policy
    MATCH (principal:AWSPrincipal{arn: $PrincipalArn})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = $aws_update_tag
    WITH policy
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(policy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    tx.run(
        ingest_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_policy(
    neo4j_session: neo4j.Session, policy_id: str, policy_name: str, policy_type: str, principal_arn: str,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_policy_tx, policy_id, policy_name, policy_type, principal_arn,
        current_aws_account_id, aws_update_tag,
    )


@timeit
def load_policy_statements(
    neo4j_session: neo4j.Session, policy_id: str, policy_name: str, statements: Any,
    aws_update_tag: int,
) -> None:
    ingest_policy_statement = """
        MATCH (policy:AWSPolicy{id: $PolicyId})
        WITH policy
        UNWIND $Statements as statement_data
        MERGE (statement:AWSPolicyStatement{id: statement_data.id})
        SET
        statement.effect = statement_data.Effect,
        statement.action = statement_data.Action,
        statement.notaction = statement_data.NotAction,
        statement.resource = statement_data.Resource,
        statement.notresource = statement_data.NotResource,
        statement.condition = statement_data.Condition,
        statement.sid = statement_data.Sid,
        statement.lastupdated = $aws_update_tag
        MERGE (policy)-[r:STATEMENT]->(statement)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """
    neo4j_session.run(
        ingest_policy_statement,
        PolicyId=policy_id,
        PolicyName=policy_name,
        Statements=statements,
        aws_update_tag=aws_update_tag,
    ).consume()


@timeit
def load_policy_data(
    neo4j_session: neo4j.Session, policy_map: Dict, policy_type: str,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM inline policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            policy_id = transform_policy_id(principal_arn, policy_type, policy_name)
            load_policy(
                neo4j_session, policy_id, policy_name, policy_type, principal_arn,
                current_aws_account_id, aws_update_tag,
            )
            load_policy_statements(neo4j_session, policy_id, policy_name, statements, aws_update_tag)


@dataclass(frozen=True)
class ServerCertificateNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('Arn')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('Arn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    upload_date: PropertyRef = PropertyRef('UploadDate')
    expiration: PropertyRef = PropertyRef('Expiration')


@dataclass(frozen=True)
class ServerCertificateToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:ServerCertificate)<-[:RESOURCE]-(:AWSAccount)
class ServerCertificateToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ServerCertificateToAWSAccountRelProperties = ServerCertificateToAWSAccountRelProperties()


@dataclass(frozen=True)
class ServerCertificateSchema(CartographyNodeSchema):
    label: str = 'ServerCertificate'
    properties: ServerCertificateNodeProperties = ServerCertificateNodeProperties()
    sub_resource_relationship: ServerCertificateToAWSAccount = ServerCertificateToAWSAccount()


@timeit
def load_server_certificates(
        neo4j_session: neo4j.Session,
        server_certificates: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading %d server certificates into graph.", len(server_certificates))

    ingestion_query = build_ingestion_query(ServerCertificateSchema())

    for cert in server_certificates:
        cert["UploadDate"] = dict_date_to_epoch(cert, "UploadDate")
        cert["Expiration"] = dict_date_to_epoch(cert, "Expiration")

    load_graph_data(
        neo4j_session,
        ingestion_query,
        server_certificates,
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


@dataclass(frozen=True)
class CredentialReportUserNodeProperties(CartographyNodeProperties):
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('arn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    user: PropertyRef = PropertyRef('user')
    arn: PropertyRef = PropertyRef('arn')
    user_creation_time: PropertyRef = PropertyRef('user_creation_time')
    password_enabled: PropertyRef = PropertyRef('password_enabled')
    password_last_used: PropertyRef = PropertyRef('password_last_used')
    password_last_changed: PropertyRef = PropertyRef('password_last_changed')
    password_next_rotation: PropertyRef = PropertyRef('password_next_rotation')
    mfa_active: PropertyRef = PropertyRef('mfa_active')
    access_key_1_active: PropertyRef = PropertyRef('access_key_1_active')
    access_key_1_last_rotated: PropertyRef = PropertyRef('access_key_1_last_rotated')
    access_key_1_last_used_date: PropertyRef = PropertyRef('access_key_1_last_used_date')
    access_key_1_last_used_region: PropertyRef = PropertyRef('access_key_1_last_used_region')
    access_key_1_last_used_service: PropertyRef = PropertyRef('access_key_1_last_used_service')
    access_key_2_active: PropertyRef = PropertyRef('access_key_2_active')
    access_key_2_last_rotated: PropertyRef = PropertyRef('access_key_2_last_rotated')
    access_key_2_last_used_date: PropertyRef = PropertyRef('access_key_2_last_used_date')
    access_key_2_last_used_region: PropertyRef = PropertyRef('access_key_2_last_used_region')
    access_key_2_last_used_service: PropertyRef = PropertyRef('access_key_2_last_used_service')
    cert_1_active: PropertyRef = PropertyRef('cert_1_active')
    cert_1_last_rotated: PropertyRef = PropertyRef('cert_1_last_rotated')
    cert_2_active: PropertyRef = PropertyRef('cert_2_active')
    cert_2_last_rotated: PropertyRef = PropertyRef('cert_2_last_rotated')


@dataclass(frozen=True)
class CredentialReportUserToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CredentialReportUser)<-[:RESOURCE]-(:AWSAccount)
class CredentialReportUserToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CredentialReportUserToAWSAccountRelProperties = CredentialReportUserToAWSAccountRelProperties()


@dataclass(frozen=True)
class CredentialReportUserSchema(CartographyNodeSchema):
    label: str = 'CredentialReportUser'
    properties: CredentialReportUserNodeProperties = CredentialReportUserNodeProperties()
    sub_resource_relationship: CredentialReportUserToAWSAccount = CredentialReportUserToAWSAccount()


@timeit
def load_credential_report_users(
    neo4j_session: neo4j.Session,
    credential_report_users: List,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info("Loading %d credential report users into graph.", len(credential_report_users))

    ingestion_query = build_ingestion_query(CredentialReportUserSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        credential_report_users,
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


@dataclass(frozen=True)
class AccountPasswordPolicyNodeProperties(CartographyNodeProperties):
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('AccountId', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    minimum_password_length: PropertyRef = PropertyRef('MinimumPasswordLength')
    require_symbols: PropertyRef = PropertyRef('RequireSymbols')
    require_numbers: PropertyRef = PropertyRef('RequireNumbers')
    require_uppercase_characters: PropertyRef = PropertyRef('RequireUppercaseCharacters')
    require_lowercase_characters: PropertyRef = PropertyRef('RequireLowercaseCharacters')
    allow_users_to_change_password: PropertyRef = PropertyRef('AllowUsersToChangePassword')
    expire_passwords: PropertyRef = PropertyRef('ExpirePasswords')
    max_password_age: PropertyRef = PropertyRef('MaxPasswordAge')
    password_reuse_prevention: PropertyRef = PropertyRef('PasswordReusePrevention')
    hard_expiry: PropertyRef = PropertyRef('HardExpiry')


@dataclass(frozen=True)
class AccountPasswordPolicyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:AccountPasswordPolicy)<-[:RESOURCE]-(:AWSAccount)
class AccountPasswordPolicyToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AccountPasswordPolicyToAWSAccountRelProperties = AccountPasswordPolicyToAWSAccountRelProperties()


@dataclass(frozen=True)
class AccountPasswordPolicySchema(CartographyNodeSchema):
    label: str = 'AccountPasswordPolicy'
    properties: AccountPasswordPolicyNodeProperties = AccountPasswordPolicyNodeProperties()
    sub_resource_relationship: AccountPasswordPolicyToAWSAccount = AccountPasswordPolicyToAWSAccount()


@timeit
def load_account_password_policy(
    neo4j_session: neo4j.Session,
    account_password_policy: Dict,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info("Loading account password policy into graph.")

    ingestion_query = build_ingestion_query(AccountPasswordPolicySchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        [account_password_policy],
        lastupdated=aws_update_tag,
        AccountId=current_aws_account_id,
    )


def load_instance_profiles(
    neo4j_session: neo4j.Session,
    instance_profiles: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(instance_profiles)} IAM instance profiles.")

    ingest_instance_profile = """
    MERGE (ip:InstanceProfile{arn: $ARN})
    ON CREATE SET ip.firstseen = timestamp()
    SET ip.lastupdated = $aws_update_tag
    WITH ip
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(ip)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    ingest_instance_profile_role_mapping = """
    MATCH (role:AWSRole{arn: $ROLE_ARN}),
    (ip:InstanceProfile{arn: $ARN})
    MERGE (ip)-[r:ASSOCIATED_WITH]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    for instance_profile in instance_profiles:
        neo4j_session.run(
            ingest_instance_profile,
            ARN=instance_profile["Arn"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        if "Roles" in instance_profile and len(instance_profile["Roles"]) > 0:
            neo4j_session.run(
                ingest_instance_profile_role_mapping,
                ROLE_ARN=instance_profile["Roles"][0]["Arn"],
                ARN=instance_profile["Arn"],
                aws_update_tag=aws_update_tag,
            )


@timeit
def sync_users(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)
    load_users(neo4j_session, data['Users'], current_aws_account_id, aws_update_tag)

    sync_user_inline_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    sync_user_managed_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    run_cleanup_job('aws_import_users_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_user_managed_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    managed_policy_data = get_user_managed_policy_data(boto3_session, data['Users'])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(
        neo4j_session, managed_policy_data, PolicyType.managed.value,
        current_aws_account_id, aws_update_tag,
    )


@timeit
def sync_user_inline_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    policy_data = get_user_policy_data(boto3_session, data['Users'])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(
        neo4j_session, policy_data, PolicyType.inline.value,
        current_aws_account_id, aws_update_tag,
    )


@timeit
def sync_groups(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)
    load_groups(neo4j_session, data['Groups'], current_aws_account_id, aws_update_tag)

    sync_groups_inline_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    sync_group_managed_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    run_cleanup_job('aws_import_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_group_managed_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(
        neo4j_session, managed_policy_data, PolicyType.managed.value,
        current_aws_account_id, aws_update_tag,
    )


def sync_groups_inline_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(
        neo4j_session, policy_data, PolicyType.inline.value,
        current_aws_account_id, aws_update_tag,
    )


@timeit
def sync_roles(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)
    load_roles(neo4j_session, data['Roles'], current_aws_account_id, aws_update_tag)

    sync_role_inline_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    sync_role_managed_policies(
        boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag,
    )

    run_cleanup_job('aws_import_roles_cleanup.json', neo4j_session, common_job_parameters)


def sync_role_managed_policies(
    boto3_session: boto3.session.Session, data: Dict,
    neo4j_session: neo4j.Session, current_aws_account_id: str, aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role managed policies for account '%s'.", current_aws_account_id)
    managed_policy_data = get_role_managed_policy_data(boto3_session, data["Roles"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(
        neo4j_session, managed_policy_data, PolicyType.managed.value,
        current_aws_account_id, aws_update_tag,
    )


def sync_role_inline_policies(
    boto3_session: boto3.session.Session, data: Dict,
    neo4j_session: neo4j.Session, current_aws_account_id: str, aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role inline policies for account '%s'.", current_aws_account_id)
    inline_policy_data = get_role_policy_data(boto3_session, data["Roles"])
    transform_policy_data(inline_policy_data, PolicyType.inline.value)
    load_policy_data(
        neo4j_session, inline_policy_data, PolicyType.inline.value,
        current_aws_account_id, aws_update_tag,
    )


@timeit
def sync_group_memberships(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM group membership for account '%s'.", current_aws_account_id)
    query = "MATCH (group:AWSGroup)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) " \
            "return group.name as name, group.arn as arn;"
    groups = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    groups_membership = {group["arn"]: get_group_membership_data(boto3_session, group["name"]) for group in groups}
    load_group_memberships(neo4j_session, groups_membership, aws_update_tag)
    run_cleanup_job(
        'aws_import_groups_membership_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_user_access_keys(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM user access keys for account '%s'.", current_aws_account_id)
    query = "MATCH (user:AWSUser)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) " \
            "RETURN user.name as name, user.arn as arn"
    for user in neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id):
        access_keys = get_account_access_key_data(boto3_session, user["name"])
        if access_keys:
            account_access_keys = {user["arn"]: access_keys}
            load_user_access_keys(neo4j_session, account_access_keys, aws_update_tag)
    run_cleanup_job(
        'aws_import_account_access_key_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_server_certificates(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM server certificates for account '%s'.", current_aws_account_id)
    server_certificates = get_server_certificates(boto3_session)
    load_server_certificates(neo4j_session, server_certificates, current_aws_account_id, aws_update_tag)
    run_cleanup_job(
        'aws_import_server_certificates_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_credential_report_users(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing credential report users for account '%s'.", current_aws_account_id)
    credential_report_content = get_credential_report_content(boto3_session)
    credential_report_users = transform_credential_report_users(credential_report_content)

    # TODO: Use the existing AWSUser / AWSPrincipal constructs instead of creating a different label
    # For simplicity of avoiding the merge, we separate it for now.
    if credential_report_content is not None:
        load_credential_report_users(
            neo4j_session,
            credential_report_users,
            current_aws_account_id,
            aws_update_tag,
        )
    run_cleanup_job(
        'aws_import_credential_report_users_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_account_password_policy(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing account password policy for account '%s'.", current_aws_account_id)
    account_password_policy = get_account_password_policy(boto3_session, current_aws_account_id)
    load_account_password_policy(
        neo4j_session,
        account_password_policy,
        current_aws_account_id,
        aws_update_tag,
    )
    run_cleanup_job(
        'aws_import_account_password_policy_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_instance_profiles(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM instance profiles for account '%s'.", current_aws_account_id)
    instance_profiles = get_instance_profiles(boto3_session)
    load_instance_profiles(
        neo4j_session,
        instance_profiles['InstanceProfiles'],
        current_aws_account_id,
        aws_update_tag,
    )
    run_cleanup_job(
        'aws_import_instance_profiles_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM for account '%s'.", current_aws_account_id)
    # This module only syncs IAM information that is in use.
    # As such only policies that are attached to a user, role or group are synced
    sync_users(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_groups(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_roles(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_group_memberships(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_assumerole_relationships(neo4j_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_server_certificates(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_credential_report_users(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_account_password_policy(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_instance_profiles(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    run_cleanup_job('aws_import_principals_cleanup.json', neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='AWSPrincipal',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )


@timeit
def get_account_from_arn(arn: str) -> str:
    # ARN documentation
    # https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html

    if not arn.startswith("arn:"):
        # must be a service principal arn, such as ec2.amazonaws.com
        return ""

    parts = arn.split(":")
    if len(parts) < 4:
        return ""
    else:
        return parts[4]

import enum
import hashlib
import json
import logging
import time
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import maya
import neo4j
import pytz
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.permission_relationships import parse_statement_node
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = 'managed'
    inline = 'inline'


class PrincipalType(enum.Enum):
    user = 'AWSUser'
    group = 'AWSGroup'
    role = 'AWSRole'


def set_used_state(session: neo4j.Session, project_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.write_transaction(_set_used_state_tx, project_id, common_job_parameters, update_tag)


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
def load_users(
    neo4j_session: neo4j.Session, users: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_user = """
    MERGE (unode:AWSUser{arn: {ARN}})
    ON CREATE SET unode:AWSPrincipal, unode.userid = {USERID}, unode.firstseen = timestamp(),
    unode.consolelink = {consolelink},
    unode.createdate = {CREATE_DATE}
    SET unode.name = {USERNAME}, unode.path = {PATH}, unode.passwordlastused = {PASSWORD_LASTUSED},
    unode.region = {region},
    unode.lastupdated = {aws_update_tag}
    WITH unode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(unode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.info(f"Loading {len(users)} IAM users.")
    for user in users:
        neo4j_session.run(
            ingest_user,
            ARN=user["Arn"],
            consolelink=aws_console_link.get_console_link(arn=user["Arn"]),
            USERID=user["UserId"],
            CREATE_DATE=str(user["CreateDate"]),
            USERNAME=user["UserName"],
            PATH=user["Path"],
            PASSWORD_LASTUSED=str(user.get("PasswordLastUsed", "")),
            AWS_ACCOUNT_ID=current_aws_account_id,
            region="global",
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_groups(
    neo4j_session: neo4j.Session, groups: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_group = """
    MERGE (gnode:AWSGroup{arn: {ARN}})
    ON CREATE SET gnode.groupid = {GROUP_ID}, gnode.firstseen = timestamp(), gnode.createdate = {CREATE_DATE}
    SET gnode:AWSPrincipal, gnode.name = {GROUP_NAME}, gnode.path = {PATH},
    gnode.region = {region},
    gnode.consolelink = {consolelink},
    gnode.lastupdated = {aws_update_tag}
    WITH gnode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(gnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.info(f"Loading {len(groups)} IAM groups to the graph.")
    for group in groups:
        neo4j_session.run(
            ingest_group,
            ARN=group["Arn"],
            consolelink=aws_console_link.get_console_link(arn=group["Arn"]),
            GROUP_ID=group["GroupId"],
            CREATE_DATE=str(group["CreateDate"]),
            GROUP_NAME=group["GroupName"],
            PATH=group["Path"],
            region="global",
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
    MERGE (rnode:AWSRole{arn: {Arn}})
    ON CREATE SET rnode:AWSPrincipal, rnode.roleid = {RoleId}, rnode.firstseen = timestamp(),
    rnode.region = {region},
    rnode.consolelink = {consolelink},
    rnode.createdate = {CreateDate}
    ON MATCH SET rnode.name = {RoleName}, rnode.path = {Path},
    rnode.lastuseddate = {LastUsedDate}, rnode.lastusedregion = {LastUsedRegion}
    SET rnode.lastupdated = {aws_update_tag}
    WITH rnode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(rnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_policy_statement = """
    MERGE (spnnode:AWSPrincipal{arn: {SpnArn}})
    ON CREATE SET spnnode.firstseen = timestamp()
    SET spnnode.lastupdated = {aws_update_tag}, spnnode.type = {SpnType}
    WITH spnnode
    MATCH (role:AWSRole{arn: {RoleArn}})
    MERGE (role)-[r:TRUSTS_AWS_PRINCIPAL]->(spnnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    # TODO support conditions
    logger.info(f"Loading {len(roles)} IAM roles to the graph.")
    for role in roles:
        neo4j_session.run(
            ingest_role,
            Arn=role["Arn"],
            consolelink=aws_console_link.get_console_link(arn=role["Arn"]),
            RoleId=role["RoleId"],
            CreateDate=str(role["CreateDate"]),
            RoleName=role["RoleName"],
            Path=role["Path"],
            region="global",
            LastUsedDate=role["RoleLastUsed"].get('LastUsedDate') if 'RoleLastUsed' in role else None,
            LastUsedRegion=role["RoleLastUsed"].get('Region') if 'RoleLastUsed' in role else None,
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


@timeit
def load_group_memberships(neo4j_session: neo4j.Session, group_memberships: Dict, aws_update_tag: int) -> None:
    ingest_membership = """
    MATCH (group:AWSGroup{arn: {GroupArn}})
    WITH group
    MATCH (user:AWSUser{arn: {PrincipalArn}})
    MERGE (user)-[r:MEMBER_AWS_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH user, group
    MATCH (group)-[:POLICY]->(policy:AWSPolicy)
    MERGE (user)-[r2:POLICY]->(policy)
    SET r2.lastupdated = {aws_update_tag}
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
    (principal:AWSPrincipal{arn:{Arn}})-[:POLICY]->
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
    neo4j_session: neo4j.Session, current_aws_account_id: str, aws_update_tag: str,
    common_job_parameters: Dict,
) -> None:
    # Must be called after load_role
    # Computes and syncs the STS_ASSUME_ROLE allow relationship
    logger.info("Syncing assume role mappings for account '%s'.", current_aws_account_id)
    query_potential_matches = """
    MATCH (:AWSAccount{id:{AccountId}})-[:RESOURCE]->(target:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(source:AWSPrincipal)
    WHERE NOT source.arn ENDS WITH 'root'
    AND NOT source.type = 'Service'
    AND NOT source.type = 'Federated'
    RETURN target.arn AS target_arn,
    source.arn AS source_arn
    """

    ingest_policies_assume_role = """
    MATCH (source:AWSPrincipal{arn: {SourceArn}})
    WITH source
    MATCH (role:AWSRole{arn: {TargetArn}})
    WITH role, source
    MERGE (source)-[r:STS_ASSUMEROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    results = neo4j_session.run(
        query_potential_matches,
        AccountId=current_aws_account_id,
    )
    potential_matches = [(r["source_arn"], r["target_arn"]) for r in results]
    for source_arn, target_arn in potential_matches:
        policies = get_policies_for_principal(neo4j_session, source_arn)
        if principal_allowed_on_resource(policies, target_arn, ["sts:AssumeRole"]):
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
def load_user_access_keys(neo4j_session: neo4j.Session, user_access_keys: Dict, aws_update_tag: int, consolelink: str) -> None:
    # TODO change the node label to reflect that this is a user access key, not an account access key
    ingest_account_key = """
    MATCH (user:AWSUser{name: {UserName}})
    WITH user
    MERGE (key:AccountAccessKey{accesskeyid: {AccessKeyId}})
    ON CREATE SET key.firstseen = timestamp(),
    key.region = {region},
    key.consolelink = {consolelink},
    key.createdate = {CreateDate}
    SET key.status = {Status}, key.lastupdated = {aws_update_tag}
    WITH user,key
    MERGE (user)-[r:AWS_ACCESS_KEY]->(key)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for username, access_keys in user_access_keys.items():
        for key in access_keys["AccessKeyMetadata"]:
            if key.get('AccessKeyId'):
                neo4j_session.run(
                    ingest_account_key,
                    consolelink = consolelink,
                    UserName=username,
                    AccessKeyId=key['AccessKeyId'],
                    CreateDate=str(key['CreateDate']),
                    Status=key['Status'],
                    region="global",
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
    MERGE (policy:AWSPolicy{id: {PolicyId}})
    ON CREATE SET
    policy.firstseen = timestamp(),
    policy.type = {PolicyType},
    policy.region = {region},
    policy.name = {PolicyName},
    policy.arn = {PolicyArn},
    policy.consolelink = {consolelink}
    SET policy.lastupdated = {aws_update_tag}
    WITH policy
    MATCH (principal:AWSPrincipal{arn: {PrincipalArn}})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = {aws_update_tag}
    """

    policy_arn = f"arn:aws:iam::{current_aws_account_id}:policy/{policy_name}"
    consolelink = aws_console_link.get_console_link(arn=policy_arn)

    tx.run(
        ingest_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        consolelink=consolelink,
        PolicyArn=policy_arn,
        region="global",
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_policy(
    neo4j_session: neo4j.Session, policy_id: str, policy_name: str, policy_type: str, principal_arn: str,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_policy_tx, policy_id, policy_name, policy_type, principal_arn, current_aws_account_id, aws_update_tag
    )


@timeit
def load_policy_statements(
    neo4j_session: neo4j.Session, policy_id: str, policy_name: str, statements: Any,
    aws_update_tag: int, consolelink: str,
) -> None:
    ingest_policy_statement = """
        MATCH (policy:AWSPolicy{id: {PolicyId}})
        WITH policy
        UNWIND {Statements} as statement_data
        MERGE (statement:AWSPolicyStatement{id: statement_data.id})
        SET
        statement.effect = statement_data.Effect,
        statement.action = statement_data.Action,
        statement.region = {region},
        statement.consolelink = {consolelink},
        statement.notaction = statement_data.NotAction,
        statement.resource = statement_data.Resource,
        statement.notresource = statement_data.NotResource,
        statement.condition = statement_data.Condition,
        statement.sid = statement_data.Sid,
        statement.lastupdated = {aws_update_tag}
        MERGE (policy)-[r:STATEMENT]->(statement)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """
    neo4j_session.run(
        ingest_policy_statement,
        PolicyId=policy_id,
        consolelink = consolelink,
        PolicyName=policy_name,
        Statements=statements,
        region="global",
        aws_update_tag=aws_update_tag,
    ).consume()


@timeit
def load_policy_data(
    neo4j_session: neo4j.Session, policy_map: Dict, policy_type: str, current_aws_account_id: str, aws_update_tag: int
) -> None:
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM inline policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            consolelink = aws_console_link.get_console_link(arn=f"arn:aws:iam::{current_aws_account_id}:policy_statement/{policy_name}")
            policy_id = transform_policy_id(principal_arn, policy_type, policy_name)
            load_policy(
                neo4j_session, policy_id, policy_name, policy_type, principal_arn, current_aws_account_id, aws_update_tag
            )
            load_policy_statements(neo4j_session, policy_id, policy_name, statements, aws_update_tag, consolelink)


@timeit
def sync_users(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)

    logger.info(f"Total Users: {len(data['Users'])}")

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(data['Users']) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam Users {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(data['Users']) or page_end == len(data['Users']):
            data['Users'] = data['Users'][page_start:]
        else:
            has_next_page = True
            data['Users'] = data['Users'][page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_users(neo4j_session, data['Users'], current_aws_account_id, aws_update_tag)

    sync_user_inline_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

    sync_user_managed_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

    # sync_user_service_access_details(boto3_session, data['Users'], neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_users_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_user_service_access_details(boto3_session, users, neo4j_session, aws_update_tag):
    for user in users:
        logger.debug(f"Syncing IAM service access details for user {user['Arn']}")
        service_access_data = get_service_access_details(boto3_session, user['Arn'])
        filtered_access_data = transform_service_access_data(service_access_data, user['Arn'])
        sync_service_access_data(neo4j_session, filtered_access_data,
                                 user['Arn'], PrincipalType.user.value, aws_update_tag)


@timeit
def sync_group_service_access_details(boto3_session, groups, neo4j_session, aws_update_tag):
    for group in groups:
        logger.debug(f"Syncing IAM service access details for group {group['Arn']}")
        service_access_data = get_service_access_details(boto3_session, group['Arn'])
        filtered_access_data = transform_service_access_data(service_access_data, group['Arn'])
        sync_service_access_data(neo4j_session, filtered_access_data,
                                 group['Arn'], PrincipalType.user.value, aws_update_tag)


@timeit
def sync_role_service_access_details(boto3_session, roles, neo4j_session, aws_update_tag):
    for role in roles:
        logger.debug(f"Syncing IAM service access details for role {role['Arn']}")
        service_access_data = get_service_access_details(boto3_session, role['Arn'])
        filtered_access_data = transform_service_access_data(service_access_data, role['Arn'])
        sync_service_access_data(neo4j_session, filtered_access_data,
                                 role['Arn'], PrincipalType.role.value, aws_update_tag)


@timeit
def get_service_access_details(both3_session, arn):
    try:
        iam_client = both3_session.client('iam')

        job = iam_client.generate_service_last_accessed_details(Arn=arn)

        response = iam_client.get_service_last_accessed_details(JobId=job['JobId'])

        cnt = 0  # the "throttling" limit so we can only ping so many requests at a time
        while response['JobStatus'] != 'COMPLETED':
            # alternately, we can use this to increase the intervals for checking
            time.sleep(30.0)
            response = iam_client.get_service_last_accessed_details(JobId=job['JobId'])
            cnt = cnt + 1
            if cnt > 5:
                break  # to ensure we are not stuck in an infinite loop

        if response['JobStatus'] != 'COMPLETED':  # credential generation could not be completed
            logger.warning("failed to get service access details after few iterations")
            return []

        access_data = response['ServicesLastAccessed']
        while response['IsTruncated']:
            response = iam_client.get_service_last_accessed_details(JobId=job['JobId'], Marker=response['Marker'])

            if 'ServicesLastAccessed':
                access_data.extend(response['ServicesLastAccessed'])

        return access_data

    except Exception as e:
        logger.warning("failed to get service access details: %s", e)

    return []


@timeit
def transform_service_access_data(service_access_data, arn):
    accesses = []
    for service_access in service_access_data:
        if 'LastAuthenticated' not in service_access:
            break

        last_authenticated = maya.parse(service_access['LastAuthenticated']).datetime()
        if pytz.utc.localize(datetime.now() - timedelta(days=90)) > last_authenticated:
            break

        access = list(filter(lambda s: s['ServiceName'] == service_access['ServiceName'], accesses))
        if len(access) == 0:
            accesses.append({
                'Id': hashlib.md5((arn + service_access['ServiceName']).encode("UTF-8")).hexdigest(),
                'ServiceName': service_access['ServiceName'],
                'ServiceNamespace': service_access['ServiceNamespace'],
                'LastAuthenticated': service_access['LastAuthenticated'],
                'LastAuthenticatedEntity': service_access['LastAuthenticatedEntity'],
                'LastAuthenticatedRegion': service_access['LastAuthenticatedRegion'],
                'TotalAuthenticatedEntities': service_access['TotalAuthenticatedEntities'],
            })

        else:
            last_authenticated = maya.parse(service_access['LastAuthenticated']).datetime()
            access_last_authenticated = maya.parse(access[0]['LastAuthenticated']).datetime()

            if access_last_authenticated < last_authenticated:
                access[0]['LastAuthenticated'] = service_access['LastAuthenticated']

    return accesses


@timeit
def sync_service_access_data(neo4j_session, access_data, principal_arn, principal_type, aws_update_tag):
    logger.debug(f"Inserting IAM service access details for principal {principal_type} {principal_arn}")

    if principal_type == PrincipalType.user.value:
        ingest_service_usage = """
        MERGE (su:AWSServiceUsage{id: {ID}})
        ON CREATE SET su.service = {SERVICE}, su.namespace= {SERVICE_NAMESPACE}, su.firstseen = timestamp()
        SET su.lastauthenticateddate = {LAST_AUTHENTICATED_DATE}, su.lastauthenticatedentity = {LAST_AUTHENTICATED_ENTITY},
        su.lastauthenticatedretion = {LAST_AUTHENTICATED_REGION}, su.totalauthenticatedentities = {TOTAL_AUTHENTICATED_ENTITIES},
        su.consolelink = {CONSOLE_LINK}, su.lastupdated = {aws_update_tag}
        WITH su
        MATCH (ap:AWSUser{arn: {PRINCIPAL_ARN}})
        MERGE (ap)-[r:HAS_ACCESSED]->(su)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """

    elif principal_type == PrincipalType.group.value:
        ingest_service_usage = """
        MERGE (su:AWSServiceUsage{id: {ID}})
        ON CREATE SET su.service = {SERVICE}, su.namespace= {SERVICE_NAMESPACE}, su.firstseen = timestamp()
        SET su.lastauthenticateddate = {LAST_AUTHENTICATED_DATE}, su.lastauthenticatedentity = {LAST_AUTHENTICATED_ENTITY},
        su.lastauthenticatedretion = {LAST_AUTHENTICATED_REGION}, su.totalauthenticatedentities = {TOTAL_AUTHENTICATED_ENTITIES},
        su.consolelink = {CONSOLE_LINK}, su.lastupdated = {aws_update_tag}
        WITH su
        MATCH (ap:AWSGroup{arn: {PRINCIPAL_ARN}})
        MERGE (ap)-[r:HAS_ACCESSED]->(su)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """

    elif principal_type == PrincipalType.role.value:
        ingest_service_usage = """
        MERGE (su:AWSServiceUsage{id: {ID}})
        ON CREATE SET su.service = {SERVICE}, su.namespace= {SERVICE_NAMESPACE}, su.firstseen = timestamp()
        SET su.lastauthenticateddate = {LAST_AUTHENTICATED_DATE}, su.lastauthenticatedentity = {LAST_AUTHENTICATED_ENTITY},
        su.lastauthenticatedretion = {LAST_AUTHENTICATED_REGION}, su.totalauthenticatedentities = {TOTAL_AUTHENTICATED_ENTITIES},
        su.consolelink = {CONSOLE_LINK}, su.lastupdated = {aws_update_tag}
        WITH su
        MATCH (ap:AWSRole{arn: {PRINCIPAL_ARN}})
        MERGE (ap)-[r:HAS_ACCESSED]->(su)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """

    for access in access_data:
        neo4j_session.run(
            ingest_service_usage,
            ID=access["Id"],
            SERVICE=access["ServiceName"],
            CONSOLE_LINK = aws_console_link.get_console_link(arn=principal_arn),
            SERVICE_NAMESPACE=access["ServiceNamespace"],
            LAST_AUTHENTICATED_DATE=access["LastAuthenticated"],
            LAST_AUTHENTICATED_ENTITY=access["LastAuthenticatedEntity"],
            LAST_AUTHENTICATED_REGION=access["LastAuthenticatedRegion"],
            TOTAL_AUTHENTICATED_ENTITIES=access["TotalAuthenticatedEntities"],
            PRINCIPAL_TYPE=principal_type,
            PRINCIPAL_ARN=principal_arn,
            aws_update_tag=aws_update_tag,
        )


@timeit
def sync_user_managed_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    managed_policy_data = get_user_managed_policy_data(boto3_session, data['Users'])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value,
                     current_aws_account_id, aws_update_tag)


@timeit
def sync_user_inline_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    policy_data = get_user_policy_data(boto3_session, data['Users'])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_groups(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)

    logger.info(f"Total Groups: {len(data['Groups'])}")

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(data['Groups']) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam Groups {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(data['Groups']) or page_end == len(data['Groups']):
            data['Groups'] = data['Groups'][page_start:]
        else:
            has_next_page = True
            data['Groups'] = data['Groups'][page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_groups(neo4j_session, data['Groups'], current_aws_account_id, aws_update_tag)

    sync_groups_inline_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

    sync_group_managed_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

    # sync_group_service_access_details(boto3_session, data['Groups'], neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_group_managed_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value,
                     current_aws_account_id, aws_update_tag)


def sync_groups_inline_policies(
    boto3_session: boto3.session.Session, data: Dict, neo4j_session: neo4j.Session,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_roles(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)

    logger.info(f"Total Roles: {len(data['Roles'])}")

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(data['Roles']) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam Roles {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(data['Roles']) or page_end == len(data['Roles']):
            data['Roles'] = data['Roles'][page_start:]
        else:
            has_next_page = True
            data['Roles'] = data['Roles'][page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_roles(neo4j_session, data['Roles'], current_aws_account_id, aws_update_tag)

    sync_role_inline_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

    sync_role_managed_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

    # sync_role_service_access_details(boto3_session, data['Roles'], neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_roles_cleanup.json', neo4j_session, common_job_parameters)


def sync_role_managed_policies(
    current_aws_account_id: str, boto3_session: boto3.session.Session, data: Dict,
    neo4j_session: neo4j.Session, aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role managed policies for account '%s'.", current_aws_account_id)
    managed_policy_data = get_role_managed_policy_data(boto3_session, data["Roles"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value,
                     current_aws_account_id, aws_update_tag)


def sync_role_inline_policies(
    current_aws_account_id: str, boto3_session: boto3.session.Session, data: Dict,
    neo4j_session: neo4j.Session, aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role inline policies for account '%s'.", current_aws_account_id)
    inline_policy_data = get_role_policy_data(boto3_session, data["Roles"])
    transform_policy_data(inline_policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, inline_policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_group_memberships(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM group membership for account '%s'.", current_aws_account_id)
    query = "MATCH (group:AWSGroup)<-[:RESOURCE]-(:AWSAccount{id: {AWS_ACCOUNT_ID}}) " \
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
    query = "MATCH (user:AWSUser)<-[:RESOURCE]-(:AWSAccount{id: {AWS_ACCOUNT_ID}}) return user.name as name"
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    usernames = [r['name'] for r in result]
    for name in usernames:
        access_keys = get_account_access_key_data(boto3_session, name)
        if access_keys:
            consolelink = aws_console_link.get_console_link(arn=f"arn:aws:iam::{current_aws_account_id}:access_keys/{name}")
            account_access_keys = {name: access_keys}
            load_user_access_keys(neo4j_session, account_access_keys, aws_update_tag, consolelink)
    run_cleanup_job(
        'aws_import_account_access_key_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def _set_used_state_tx(
    tx: neo4j.Transaction, project_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: {WORKSPACE_ID}})-[:OWNER]->
    (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(n:AWSRole)
    WHERE (n)-[:TRUSTS_AWS_PRINCIPAL]->() AND n.lastupdated = {update_tag}
    SET n.isUsed = {isUsed}
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=True,
    )

    ingest_entity_used = """
    MATCH (:CloudanixWorkspace{id: {WORKSPACE_ID}})-[:OWNER]->
    (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(n)
    WHERE ()-[:TRUSTS_AWS_PRINCIPAL]->(n) AND n.lastupdated = {update_tag}
    AND labels(n) IN [['AWSUser'], ['AWSGroup']]
    SET n.isUsed = {isUsed}
    """

    tx.run(
        ingest_entity_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: {WORKSPACE_ID}})-[:OWNER]->
    (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(n)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = {update_tag}
    AND labels(n) IN [['AWSUser'], ['AWSGroup'], ['AWSRole']]
    SET n.isUsed = {isUsed}
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=False,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing IAM for account '%s', at %s.", current_aws_account_id, tic)
    # This module only syncs IAM information that is in use.
    # As such only policies that are attached to a user, role or group are synced
    sync_users(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_groups(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_roles(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        if not common_job_parameters.get('pagination', {}).get('iam', {}).get('hasNextPage', False):
            sync_group_memberships(neo4j_session, boto3_session, current_aws_account_id,
                                   update_tag, common_job_parameters)
            sync_assumerole_relationships(neo4j_session, current_aws_account_id, update_tag, common_job_parameters)
            sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id,
                                  update_tag, common_job_parameters)
            set_used_state(neo4j_session, current_aws_account_id, common_job_parameters, update_tag)
    else:
        sync_group_memberships(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
        sync_assumerole_relationships(neo4j_session, current_aws_account_id, update_tag, common_job_parameters)
        sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
        set_used_state(neo4j_session, current_aws_account_id, common_job_parameters, update_tag)

    run_cleanup_job('aws_import_principals_cleanup.json', neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process IAM: {toc - tic:0.4f} seconds")

# https://docs.aws.amazon.com/cli/latest/reference/iam/generate-service-last-accessed-details.html
#
#
# Steps to get access details:
# 1.generate service last accessed details by ARN (or overall?)
# 2.
#
#

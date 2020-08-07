import enum
import json
import logging

from cartography.intel.aws.permission_relationships import parse_statement_node
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = 'managed'
    inline = 'inline'


@timeit
def get_group_policies(boto3_session, group_name):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_group_policies')
    policy_names = []
    for page in paginator.paginate(GroupName=group_name):
        policy_names.extend(page['PolicyNames'])
    return {'PolicyNames': policy_names}


@timeit
def get_group_policy_info(boto3_session, group_name, policy_name):
    client = boto3_session.client('iam')
    return client.get_group_policy(GroupName=group_name, PolicyName=policy_name)


@timeit
def get_group_membership_data(boto3_session, group_name):
    client = boto3_session.client('iam')
    try:
        memberships = client.get_group(GroupName=group_name)
        return memberships
    except client.exceptions.NoSuchEntityException:
        # Avoid crashing the sync
        logger.warning("client.get_group(GroupName='%s') failed with NoSuchEntityException; skipping.", group_name)
        return {}


@timeit
def get_group_policy_data(boto3_session, group_list):
    resource_client = boto3_session.resource('iam')
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[arn] = policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_group.policies.all()}
    return policies


@timeit
def get_group_managed_policy_data(boto3_session, group_list):
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
def get_user_policy_data(boto3_session, user_list):
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
def get_user_managed_policy_data(boto3_session, user_list):
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
def get_role_policy_data(boto3_session, role_list):
    resource_client = boto3_session.resource('iam')
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        arn = role["Arn"]
        resource_role = resource_client.Role(name)
        policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_role.policies.all()}
    return policies


@timeit
def get_role_managed_policy_data(boto3_session, role_list):
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
def get_user_list_data(boto3_session):
    client = boto3_session.client('iam')

    paginator = client.get_paginator('list_users')
    users = []
    for page in paginator.paginate():
        users.extend(page['Users'])
    return {'Users': users}


@timeit
def get_group_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_groups')
    groups = []
    for page in paginator.paginate():
        groups.extend(page['Groups'])
    return {'Groups': groups}


@timeit
def get_role_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_roles')
    roles = []
    for page in paginator.paginate():
        roles.extend(page['Roles'])
    return {'Roles': roles}


@timeit
def get_account_access_key_data(boto3_session, username):
    client = boto3_session.client('iam')
    # NOTE we can get away without using a paginator here because users are limited to two access keys
    access_keys = {}
    try:
        access_keys = client.list_access_keys(UserName=username)
    except client.exceptions.NoSuchEntityException:
        logger.warning(
            f"Could not get access key for user {username} due to NoSuchEntityException; skipping.",
        )
    return access_keys


@timeit
def load_users(neo4j_session, users, current_aws_account_id, aws_update_tag):
    ingest_user = """
    MERGE (unode:AWSUser{arn: {ARN}})
    ON CREATE SET unode:AWSPrincipal, unode.userid = {USERID}, unode.firstseen = timestamp(),
    unode.createdate = {CREATE_DATE}
    SET unode.name = {USERNAME}, unode.path = {PATH}, unode.passwordlastused = {PASSWORD_LASTUSED},
    unode.lastupdated = {aws_update_tag}
    WITH unode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(unode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

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
def load_groups(neo4j_session, groups, current_aws_account_id, aws_update_tag):
    ingest_group = """
    MERGE (gnode:AWSGroup{arn: {ARN}})
    ON CREATE SET gnode.groupid = {GROUP_ID}, gnode.firstseen = timestamp(), gnode.createdate = {CREATE_DATE}
    SET gnode:AWSPrincipal, gnode.name = {GROUP_NAME}, gnode.path = {PATH},gnode.lastupdated = {aws_update_tag}
    WITH gnode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(gnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

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


def _parse_principal_entries(principal):
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
def load_roles(neo4j_session, roles, current_aws_account_id, aws_update_tag):
    ingest_role = """
    MERGE (rnode:AWSRole{arn: {Arn}})
    ON CREATE SET rnode:AWSPrincipal, rnode.roleid = {RoleId}, rnode.firstseen = timestamp(),
    rnode.createdate = {CreateDate}
    ON MATCH SET rnode.name = {RoleName}, rnode.path = {Path}
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


@timeit
def load_group_memberships(neo4j_session, group_memberships, aws_update_tag):
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
def get_policies_for_principal(neo4j_session, principal_arn):
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
def sync_assumerole_relationships(neo4j_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    # Must be called after load_role
    # Computes and syncs the STS_ASSUME_ROLE allow relationship
    logger.debug("Syncing assume role for account '%s'.", current_aws_account_id)
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
def load_user_access_keys(neo4j_session, user_access_keys, aws_update_tag):
    # TODO change the node label to reflect that this is a user access key, not an account access key
    ingest_account_key = """
    MATCH (user:AWSUser{name: {UserName}})
    WITH user
    MERGE (key:AccountAccessKey{accesskeyid: {AccessKeyId}})
    ON CREATE SET key.firstseen = timestamp(), key.createdate = {CreateDate}
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
                    UserName=username,
                    AccessKeyId=key['AccessKeyId'],
                    CreateDate=str(key['CreateDate']),
                    Status=key['Status'],
                    aws_update_tag=aws_update_tag,
                )


def ensure_list(obj):
    if not isinstance(obj, list):
        obj = [obj]
    return obj


def _transform_policy_statements(statements, policy_id):
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


def transform_policy_data(policy_map, policy_type):
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM {policy_type} policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            policy_id = transform_policy_id(principal_arn, policy_type, policy_name)
            statements = _transform_policy_statements(
                statements, policy_id,
            )


def transform_policy_id(principal_arn, policy_type, name):
    return f"{principal_arn}/{policy_type}_policy/{name}"


@timeit
def load_policy(neo4j_session, policy_id, policy_name, policy_type, principal_arn, aws_update_tag):
    injest_policy = """
    MERGE (policy:AWSPolicy{id: {PolicyId}})
    ON CREATE SET
    policy.firstseen = timestamp(),
    policy.type = {PolicyType},
    policy.name = {PolicyName}
    SET
    policy.lastupdated = {aws_update_tag}
    WITH policy
    MATCH (principal:AWSPrincipal{arn: {PrincipalArn}})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        injest_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        aws_update_tag=aws_update_tag,
    ).consume()


@timeit
def load_policy_statements(neo4j_session, policy_id, policy_name, statements, aws_update_tag):
    injest_policy_statement = """
        MATCH (policy:AWSPolicy{id: {PolicyId}})
        WITH policy
        UNWIND {Statements} as statement_data
        MERGE (statement:AWSPolicyStatement{id: statement_data.id})
        SET
        statement.effect = statement_data.Effect,
        statement.action = statement_data.Action,
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
        injest_policy_statement,
        PolicyId=policy_id,
        PolicyName=policy_name,
        Statements=statements,
        aws_update_tag=aws_update_tag,
    ).consume()


@timeit
def load_policy_data(neo4j_session, policy_map, policy_type, aws_update_tag):
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM inline policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            policy_id = transform_policy_id(principal_arn, policy_type, policy_name)
            load_policy(neo4j_session, policy_id, policy_name, policy_type, principal_arn, aws_update_tag)
            load_policy_statements(neo4j_session, policy_id, policy_name, statements, aws_update_tag)


@timeit
def sync_users(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)
    load_users(neo4j_session, data['Users'], current_aws_account_id, aws_update_tag)

    sync_user_inline_policies(boto3_session, data, neo4j_session, aws_update_tag)

    sync_user_managed_policies(boto3_session, data, neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_users_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_user_managed_policies(boto3_session, data, neo4j_session, aws_update_tag):
    managed_policy_data = get_user_managed_policy_data(boto3_session, data['Users'])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value, aws_update_tag)


@timeit
def sync_user_inline_policies(boto3_session, data, neo4j_session, aws_update_tag):
    policy_data = get_user_policy_data(boto3_session, data['Users'])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, aws_update_tag)


@timeit
def sync_groups(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)
    load_groups(neo4j_session, data['Groups'], current_aws_account_id, aws_update_tag)

    sync_groups_inline_policies(boto3_session, data, neo4j_session, aws_update_tag)

    sync_group_managed_policies(boto3_session, data, neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_group_managed_policies(boto3_session, data, neo4j_session, aws_update_tag):
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value, aws_update_tag)


def sync_groups_inline_policies(boto3_session, data, neo4j_session, aws_update_tag):
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transform_policy_data(policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, aws_update_tag)


@timeit
def sync_roles(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)
    load_roles(neo4j_session, data['Roles'], current_aws_account_id, aws_update_tag)

    sync_role_inline_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

    sync_role_managed_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

    run_cleanup_job('aws_import_roles_cleanup.json', neo4j_session, common_job_parameters)


def sync_role_managed_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag):
    logger.debug("Syncing IAM role managed policies for account '%s'.", current_aws_account_id)
    managed_policy_data = get_role_managed_policy_data(boto3_session, data["Roles"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value)
    load_policy_data(neo4j_session, managed_policy_data, PolicyType.managed.value, aws_update_tag)


def sync_role_inline_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag):
    logger.debug("Syncing IAM role inline policies for account '%s'.", current_aws_account_id)
    inline_policy_data = get_role_policy_data(boto3_session, data["Roles"])
    transform_policy_data(inline_policy_data, PolicyType.inline.value)
    load_policy_data(neo4j_session, inline_policy_data, PolicyType.inline.value, aws_update_tag)


@timeit
def sync_group_memberships(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM group membership for account '%s'.", current_aws_account_id)
    query = "MATCH (group:AWSGroup)<-[:RESOURCE]-(AWSAccount{id: {AWS_ACCOUNT_ID}}) " \
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
def sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM user access keys for account '%s'.", current_aws_account_id)
    query = "MATCH (user:AWSUser)<-[:RESOURCE]-(AWSAccount{id: {AWS_ACCOUNT_ID}}) return user.name as name"
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    usernames = [r['name'] for r in result]
    for name in usernames:
        access_keys = get_account_access_key_data(boto3_session, name)
        if access_keys:
            account_access_keys = {name: access_keys}
            load_user_access_keys(neo4j_session, account_access_keys, aws_update_tag)
    run_cleanup_job(
        'aws_import_account_access_key_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing IAM for account '%s'.", account_id)
    # This module only syncs IAM information that is in use.
    # As such only policies that are attached to a user, role or group are synced
    sync_users(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_groups(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_roles(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_group_memberships(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_assumerole_relationships(neo4j_session, account_id, update_tag, common_job_parameters)
    sync_user_access_keys(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    run_cleanup_job('aws_import_principals_cleanup.json', neo4j_session, common_job_parameters)

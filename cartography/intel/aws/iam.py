import logging

import policyuniverse.statement

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_group_policies(boto3_session, group_name):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_group_policies')
    policy_names = []
    for page in paginator.paginate(GroupName=group_name):
        policy_names.extend(page['PolicyNames'])
    return {'PolicyNames': policy_names}


def get_group_policy_info(boto3_session, group_name, policy_name):
    client = boto3_session.client('iam')
    return client.get_group_policy(GroupName=group_name, PolicyName=policy_name)


def get_group_membership_data(boto3_session, group_name):
    client = boto3_session.client('iam')
    return client.get_group(GroupName=group_name)


def get_user_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_users')
    users = []
    for page in paginator.paginate():
        users.extend(page['Users'])
    return {'Users': users}


def get_group_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_groups')
    groups = []
    for page in paginator.paginate():
        groups.extend(page['Groups'])
    return {'Groups': groups}


def get_policy_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_policies')
    policies = []
    for page in paginator.paginate():
        policies.extend(page['Policies'])
    return {'Policies': policies}


def get_role_list_data(boto3_session):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_roles')
    roles = []
    for page in paginator.paginate():
        roles.extend(page['Roles'])
    return {'Roles': roles}


def get_role_policies(boto3_session, role_name):
    client = boto3_session.client('iam')
    paginator = client.get_paginator('list_role_policies')
    policy_names = []
    for page in paginator.paginate(RoleName=role_name):
        policy_names.extend(page['PolicyNames'])
    return {'PolicyNames': policy_names}


def get_role_policy_info(boto3_session, role_name, policy_name):
    client = boto3_session.client('iam')
    return client.get_role_policy(RoleName=role_name, PolicyName=policy_name)


def get_account_access_key_data(boto3_session, username):
    client = boto3_session.client('iam')
    # NOTE we can get away without using a paginator here because users are limited to two access keys
    return client.list_access_keys(UserName=username)


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


def load_groups(neo4j_session, groups, current_aws_account_id, aws_update_tag):
    ingest_group = """
    MERGE (gnode:AWSGroup{arn: {ARN}})
    ON CREATE SET gnode.groupid = {GROUP_ID}, gnode.firstseen = timestamp(), gnode.createdate = {CREATE_DATE}
    SET gnode.name = {GROUP_NAME}, gnode.path = {PATH},gnode.lastupdated = {aws_update_tag}
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


def load_policies(neo4j_session, policies, current_aws_account_id, aws_update_tag):
    ingest_policy = """
    MERGE (pnode:AWSPolicy{arn: {ARN}})
    ON CREATE SET pnode.policyid = {POLICY_ID}, pnode.firstseen = timestamp(), pnode.createdate = {CREATE_DATE}
    SET pnode.name = {POLICY_NAME}, pnode.path = {PATH}, pnode.defaultversionid = {DEFAULT_VERSION_ID},
    pnode.updatedate = {POLICY_UPDATE}, pnode.isattachable = {IS_ATTACHABLE},
    pnode.attachmentcount = {ATTACHMENT_COUNT},
    pnode.lastupdated = {aws_update_tag}
    WITH pnode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:AWS_POLICY]->(pnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for policy in policies:
        neo4j_session.run(
            ingest_policy,
            ARN=policy["Arn"],
            POLICY_ID=policy["PolicyId"],
            POLICY_NAME=policy["PolicyName"],
            PATH=policy["Path"],
            DEFAULT_VERSION_ID=policy["DefaultVersionId"],
            CREATE_DATE=str(policy["CreateDate"]),
            POLICY_UPDATE=str(policy["UpdateDate"]),
            IS_ATTACHABLE=policy["IsAttachable"],
            ATTACHMENT_COUNT=policy["AttachmentCount"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


def load_roles(neo4j_session, roles, current_aws_account_id, aws_update_tag):
    ingest_role = """
    MERGE (rnode:AWSRole{arn: {Arn}})
    ON CREATE SET rnode:AWSPrincipal, rnode.roleid = {RoleId}, rnode.firstseen = timestamp(),
    rnode.createdate = {CreateDate}
    ON MATCH SET rnode.name = {RoleName}, rnode.path = {Path}
    SET rnode.lastupdated = {aws_update_tag}
    WITH rnode
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:AWS_ROLE]->(rnode)
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
            principal = statement["Principal"]
            principal_values = []
            if 'AWS' in principal:
                principal_type, principal_values = 'AWS', principal['AWS']
            elif 'Service' in principal:
                principal_type, principal_values = 'Service', principal['Service']
            elif 'Federated' in principal:
                principal_type, principal_values = 'Federated', principal['Federated']
            if not isinstance(principal_values, list):
                principal_values = [principal_values]
            for principal_value in principal_values:
                neo4j_session.run(
                    ingest_policy_statement,
                    SpnArn=principal_value,
                    SpnType=principal_type,
                    RoleArn=role['Arn'],
                    aws_update_tag=aws_update_tag,
                )


def load_group_memberships(neo4j_session, group_memberships, aws_update_tag):
    ingest_membership = """
    MATCH (group:AWSGroup{arn: {GroupArn}})
    WITH group
    MATCH (user:AWSUser{arn: {PrincipalArn}})
    MERGE (user)-[r:MEMBER_AWS_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for group_arn, membership_data in group_memberships.items():
        for info in membership_data["Users"]:
            principal_arn = info["Arn"]
            neo4j_session.run(
                ingest_membership,
                GroupArn=group_arn,
                PrincipalArn=principal_arn,
                aws_update_tag=aws_update_tag,
            )


def _find_roles_assumable_in_policy(policy_data):
    ret = []
    statements = policy_data["PolicyDocument"]["Statement"]
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        parsed_statement = policyuniverse.statement.Statement(statement)
        if parsed_statement.effect == 'Allow' and 'sts:assumerole' in parsed_statement.actions_expanded:
            ret.extend(list(parsed_statement.resources))
    return ret


def load_group_policies(neo4j_session, group_policies, aws_update_tag):
    ingest_policies_assume_role = """
    MATCH (group:AWSGroup{name: {GroupName}})
    WITH group
    MERGE (role:AWSRole{arn: {RoleArn}})
    ON CREATE SET role.firstseen = timestamp()
    SET role.lastupdated = {aws_update_tag}
    WITH role, group
    MERGE (group)-[r:STS_ASSUMEROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for group_name, policies in group_policies.items():
        for policy_name, policy_data in policies.items():
            for role_arn in _find_roles_assumable_in_policy(policy_data):
                # TODO resource ARNs may contain wildcards, e.g. arn:aws:iam::*:role/admin --
                # TODO policyuniverse can't expand resource wildcards so further thought is needed here
                neo4j_session.run(
                    ingest_policies_assume_role,
                    GroupName=group_name,
                    RoleArn=role_arn,
                    aws_update_tag=aws_update_tag,
                )


def load_role_policies(neo4j_session, role_policies, aws_update_tag):
    ingest_policies_assume_role = """
    MATCH (assumer:AWSRole{name: {RoleName}})
    WITH assumer
    MERGE (role:AWSRole{arn: {RoleArn}})
    ON CREATE SET role.firstseen = timestamp()
    SET role.lastupdated = {aws_update_tag}
    WITH role, assumer
    MERGE (assumer)-[r:STS_ASSUMEROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for role_name, policies in role_policies.items():
        for policy_name, policy_data in policies.items():
            for role_arn in _find_roles_assumable_in_policy(policy_data):
                # TODO resource ARNs may contain wildcards, e.g. arn:aws:iam::*:role/admin --
                # TODO policyuniverse can't expand resource wildcards so further thought is needed here
                neo4j_session.run(
                    ingest_policies_assume_role,
                    RoleName=role_name,
                    RoleArn=role_arn,
                    aws_update_tag=aws_update_tag,
                )


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


def sync_users(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)
    load_users(neo4j_session, data['Users'], current_aws_account_id, aws_update_tag)
    run_cleanup_job('aws_import_users_cleanup.json', neo4j_session, common_job_parameters)


def sync_groups(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)
    load_groups(neo4j_session, data['Groups'], current_aws_account_id, aws_update_tag)
    run_cleanup_job('aws_import_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_policies(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM policies for account '%s'.", current_aws_account_id)
    data = get_policy_list_data(boto3_session)
    load_policies(neo4j_session, data['Policies'], current_aws_account_id, aws_update_tag)
    run_cleanup_job('aws_import_policies_cleanup.json', neo4j_session, common_job_parameters)


def sync_roles(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)
    load_roles(neo4j_session, data['Roles'], current_aws_account_id, aws_update_tag)
    run_cleanup_job('aws_import_roles_cleanup.json', neo4j_session, common_job_parameters)


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


def sync_group_policies(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM group policies for account '%s'.", current_aws_account_id)
    query = "MATCH (group:AWSGroup)<-[:RESOURCE]-(AWSAccount{id: {AWS_ACCOUNT_ID}}) return group.name as name;"
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    groups = [r['name'] for r in result]
    groups_policies = {}
    for group_name in groups:
        groups_policies[group_name] = {}
        for policy_name in get_group_policies(boto3_session, group_name)['PolicyNames']:
            groups_policies[group_name][policy_name] = get_group_policy_info(boto3_session, group_name, policy_name)
    load_group_policies(neo4j_session, groups_policies, aws_update_tag)
    run_cleanup_job(
        'aws_import_groups_policy_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def sync_role_policies(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM role policies for account '%s'.", current_aws_account_id)
    query = """
    MATCH (role:AWSRole)<-[:AWS_ROLE]-(AWSAccount{id: {AWS_ACCOUNT_ID}})
    WHERE exists(role.name)
    RETURN role.name AS name;
    """
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    roles = [r['name'] for r in result]
    roles_policies = {}
    for role_name in roles:
        roles_policies[role_name] = {}
        for policy_name in get_role_policies(boto3_session, role_name)['PolicyNames']:
            roles_policies[role_name][policy_name] = get_role_policy_info(boto3_session, role_name, policy_name)
    load_role_policies(neo4j_session, roles_policies, aws_update_tag)
    run_cleanup_job(
        'aws_import_roles_policy_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id, aws_update_tag, common_job_parameters):
    logger.debug("Syncing IAM user access keys for account '%s'.", current_aws_account_id)
    query = "MATCH (user:AWSUser)<-[:RESOURCE]-(AWSAccount{id: {AWS_ACCOUNT_ID}}) return user.name as name"
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    usernames = [r['name'] for r in result]
    account_access_key = {name: get_account_access_key_data(boto3_session, name) for name in usernames}
    load_user_access_keys(neo4j_session, account_access_key, aws_update_tag)
    run_cleanup_job(
        'aws_import_account_access_key_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def sync(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing IAM for account '%s'.", account_id)
    sync_users(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_groups(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_policies(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_roles(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_group_memberships(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_group_policies(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_role_policies(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    sync_user_access_keys(neo4j_session, boto3_session, account_id, update_tag, common_job_parameters)
    run_cleanup_job('aws_import_principals_cleanup.json', neo4j_session, common_job_parameters)

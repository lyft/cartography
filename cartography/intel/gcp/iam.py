import json
import logging
import time
from typing import Dict
from typing import List
from datetime import datetime

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


def set_used_state(session: neo4j.Session, project_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.write_transaction(_set_used_state_tx, project_id, common_job_parameters, update_tag)


@timeit
def get_service_accounts(iam: Resource, project_id: str) -> List[Dict]:
    service_accounts: List[Dict] = []
    try:
        req = iam.projects().serviceAccounts().list(name=f'projects/{project_id}')
        while req is not None:
            res = req.execute()
            page = res.get('accounts', [])
            service_accounts.extend(page)
            req = iam.projects().serviceAccounts().list_next(previous_request=req, previous_response=res)

        return service_accounts
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve service accounts on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_service_accounts(service_accounts: List[Dict], project_id: str) -> List[Dict]:
    for account in service_accounts:
        account['firstName'] = account['name'].split('@')[0]
        account['id'] = account['email']
        account['service_account_name'] = account['name'].split('/')[-1]
        account['consolelink'] = gcp_console_link.get_console_link(
            resource_name='service_account', project_id=project_id, service_account_unique_id=account['uniqueId'],
        )
    return service_accounts


@timeit
def get_service_account_keys(iam: Resource, project_id: str, service_account: Dict) -> List[Dict]:
    service_keys: List[Dict] = []
    try:
        res = iam.projects().serviceAccounts().keys().list(name=service_account['name']).execute()
        keys = res.get('keys', [])
        for key in keys:
            key['id'] = key['name'].split('/')[-1]
            key['service_account_key_name'] = key['name'].split('/')[-1]
            key['serviceaccount'] = service_account['name']
            key['consolelink'] = gcp_console_link.get_console_link(
                resource_name='service_account_key', project_id=project_id, service_account_unique_id=service_account['uniqueId'],
            )

        service_keys.extend(keys)

        return service_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve Keys on project %s & account %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, service_account['name'], err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_predefined_roles(iam: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = iam.roles().list(view="FULL")
        while req is not None:
            res = req.execute()
            page = res.get('roles', [])
            roles.extend(page)
            req = iam.roles().list_next(previous_request=req, previous_response=res)

        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve predefined roles on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def get_organization_custom_roles(iam: Resource, crm_v1: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = crm_v1.projects().get(projectId=project_id)
        res_project = req.execute()
        if res_project.get('parent').get('type') == 'organization':
            req = iam.organizations().roles().list(
                parent=f"organizations/{res_project.get('parent').get('id')}", view="FULL")
            while req is not None:
                res = req.execute()
                page = res.get('roles', [])
                roles.extend(page)
                req = iam.organizations().roles().list_next(previous_request=req, previous_response=res)
        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve organization custom roles on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def get_project_custom_roles(iam: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = iam.projects().roles().list(parent=f'projects/{project_id}', view="FULL")
        while req is not None:
            res = req.execute()
            page = res.get('roles', [])
            roles.extend(page)
            req = iam.projects().roles().list_next(previous_request=req, previous_response=res)

        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve project custom role on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def transform_roles(roles_list: List[Dict], project_id: str, type: str) -> List[Dict]:
    for role in roles_list:
        role['id'] = get_role_id(role['name'], project_id)
        role['type'] = type
        role['parent'] = 'project'
        role['parent_id'] = f"projects/{project_id}"
        if role['name'].startswith('organizations/'):
            role['parent'] = 'organization'
            role['parent_id'] = f"organizations/{role['name'].split('/')[1]}"
        role['consolelink'] = gcp_console_link.get_console_link(
            resource_name='iam_role', project_id=project_id, role_id=role['name'],
        )
    return roles_list


@timeit
def get_role_id(role_name: str, project_id: str) -> str:
    if role_name.startswith('organizations/'):
        return role_name

    elif role_name.startswith('projects/'):
        return role_name

    elif role_name.startswith('roles/'):
        return f'projects/{project_id}/{role_name}'
    return ''


@timeit
def get_policy_bindings(crm_v1: Resource, crm_v2: Resource, project_id: str) -> List[Dict]:
    try:
        bindings = []

        req = crm_v1.projects().getIamPolicy(resource=project_id, body={'options': {'requestedPolicyVersion': 3}})
        res = req.execute()
        if res.get('bindings'):
            for binding in res['bindings']:
                binding['parent'] = 'project'
                binding['parent_id'] = f"projects/{project_id}"
                bindings.append(binding)

        req = crm_v1.projects().get(projectId=project_id)
        res_project = req.execute()
        if res_project.get('parent').get('type') == 'organization':
            req = crm_v1.organizations().getIamPolicy(resource=f"organizations/{res_project.get('parent').get('id')}")
            res = req.execute()
            if res.get('bindings'):
                for binding in res['bindings']:
                    binding['parent'] = 'organization'
                    binding['parent_id'] = f"organizations/{res_project.get('parent').get('id')}"
                    bindings.append(binding)
        elif res_project.get('parent').get('type') == 'folder':
            req = crm_v2.folders().getIamPolicy(resource=f"folders/{res_project.get('parent').get('id')}")
            res = req.execute()
            if res.get('bindings'):
                for binding in res['bindings']:
                    binding['parent'] = 'folder'
                    binding['parent_id'] = f"folders/{res_project.get('parent').get('id')}"
                    bindings.append(binding)

        return bindings
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve policy bindings on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return bindings
        else:
            raise


def transform_bindings(bindings: Dict, project_id: str) -> tuple:
    users = []
    groups = []
    domains = []
    service_account = []
    entity_list = []
    public_access = False
    for binding in bindings:
        for member in binding['members']:
            if member.startswith('allUsers') or member.startswith('allAuthenticatedUsers'):
                public_access = True
            else:
                if member.startswith('user:'):
                    usr = member[len('user:'):]
                    users.append({
                        "id": f'projects/{project_id}/users/{usr}',
                        "email": usr,
                        "name": usr.split("@")[0],
                    })

                elif member.startswith('group:'):
                    grp = member[len('group:'):]
                    groups.append({
                        "id": f'projects/{project_id}/groups/{grp}',
                        "email": grp,
                        "name": grp.split('@')[0],
                    })

                elif member.startswith('domain:'):
                    dmn = member[len('domain:'):]
                    domains.append({
                        "id": f'projects/{project_id}/domains/{dmn}',
                        "email": dmn,
                        "name": dmn,
                    })

                elif member.startswith('serviceAccount:'):
                    sac = member[len('serviceAccount:'):]
                    service_account.append({
                        "id": f'projects/{project_id}/service_account/{sac}',
                        "email": sac,
                        "name": sac,
                    })

    entity_list.extend(users)
    entity_list.extend(groups)
    entity_list.extend(domains)
    entity_list.extend(service_account)
    # return (
    #     [dict(s) for s in {frozenset(d.items()) for d in users}],
    #     [dict(s) for s in {frozenset(d.items()) for d in groups}],
    #     [dict(s) for s in {frozenset(d.items()) for d in domains}],
    # )
    return entity_list, public_access


@timeit
def get_apikeys_keys(apikey: Resource, project_id: str) -> List[Resource]:
    api_keys = []
    try:
        req = apikey.projects().locations().keys().list(parent=f"projects/{project_id}/locations/global")
        while req is not None:
            res = req.execute()
            if 'keys' in res:
                api_keys.extend(res['keys'])
            req = apikey.projects().locations().keys().list_next(previous_request=req, previous_response=res)

        return api_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve api keys on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_api_keys(apikeys: List, project_id: str) -> List[Dict]:
    list_keys = []

    for key in apikeys:
        key['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, api_key_id=key['uid'], resource_name='api_key')
        key['id'] = key['name']
        list_keys.append(key)

    return list_keys


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session, api_keys: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $ApiKeys as key
    MERGE (apikey:GCPApiKey{id: key.id})
    ON CREATE SET
        apikey.firstseen = timestamp()
    SET
        apikey.lastupdated = $gcp_update_tag,
        apikey.uniqueId = key.name,
        apikey.consolelink = key.consolelink,
        apikey.region = key.region,
        apikey.updateTime = key.updateTime,
        apikey.deleteTime = key.deleteTime
    WITH apikey
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(apikey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        query,
        ApiKeys=api_keys,
        project_id=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_keys(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_api_keys_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict], project_id: str, gcp_update_tag: int,


) -> None:
    ingest_service_accounts = """
    UNWIND $service_accounts_list AS sa
    MERGE (u:GCPServiceAccount{id: sa.id})
    ON CREATE SET u:GCPPrincipal, u.firstseen = timestamp()
    SET u.name = sa.name, u.displayname = sa.displayName,
    u.service_account_name = sa.service_account_name,
    u.create_date = $createDate,
    u.email = sa.email,
    u.consolelink = sa.consolelink,
    u.parent = $parent,
    u.parent_id = $parentId,
    u.region = $region,
    u.disabled = sa.disabled, u.serviceaccountid = sa.uniqueId,
    u.lastupdated = $gcp_update_tag
    WITH u
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_service_accounts,
        service_accounts_list=service_accounts,
        parent='project',
        parentId=f'projects/{project_id}',
        project_id=project_id,
        createDate=datetime.utcnow(),
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_service_accounts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_service_accounts_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_service_account_keys(
    neo4j_session: neo4j.Session, service_account_keys: List[Dict],
    service_account: str, gcp_update_tag: int,
) -> None:
    ingest_service_accounts = """
    UNWIND $service_account_keys_list AS sa
    MERGE (u:GCPServiceAccountKey{id: sa.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name=sa.name, u.serviceaccountid= $serviceaccount,
    u.region = $region,
    u.create_date = $createDate,
    u.keytype = sa.keyType, u.origin = sa.keyOrigin,
    u.consolelink = sa.consolelink,
    u.algorithm = sa.keyAlgorithm, u.validbeforetime = sa.validBeforeTime,

    u.validaftertime = sa.validAfterTime, u.lastupdated = $gcp_update_tag,
    u.disabled = sa.disabled
    WITH u, sa
    MATCH (d:GCPServiceAccount{id: $serviceaccount})
    MERGE (d)-[r:HAS_KEY]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_service_accounts,
        service_account_keys_list=service_account_keys,
        serviceaccount=service_account,
        createDate=datetime.utcnow(),
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_service_account_keys(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_service_account_keys_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_roles(neo4j_session: neo4j.Session, roles: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    ingest_roles = """
    UNWIND $roles_list AS d
    MERGE (u:GCPRole{id: d.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = d.name,
    u.title = d.title,
    u.region = $region,
    u.create_date = $createDate,
    u.description = d.description,
    u.deleted = d.deleted,
    u.consolelink = d.consolelink,
    u.type = d.type,
    u.parent = d.parent,
    u.parent_id = d.parent_id,
    u.permissions = d.includedPermissions,
    u.roleid = d.id,
    u.lastupdated = $gcp_update_tag
    WITH u
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_roles,
        roles_list=roles,
        region="global",
        createDate=datetime.utcnow(),
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_roles_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_bindings(neo4j_session: neo4j.Session, bindings: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    for binding in bindings:
        role_id = get_role_id(binding['role'], project_id)

        for member in binding['members']:
            if member.startswith('user:'):
                usr = member[len('user:'):]
                user = {
                    'id': usr,
                    "email": usr,
                    "name": usr.split("@")[0],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_user'),

                }
                attach_role_to_user(
                    neo4j_session, role_id, user,
                    project_id, gcp_update_tag,
                )

            elif member.startswith('serviceAccount:'):
                serviceAccount = {
                    'id': member[len('serviceAccount:'):],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                }
                attach_role_to_service_account(
                    neo4j_session,
                    role_id, serviceAccount,
                    project_id,
                    gcp_update_tag,
                )

            elif member.startswith('group:'):
                grp = member[len('group:'):]
                group = {
                    "id": grp,
                    "email": grp,
                    "name": grp.split('@')[0],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_group'),
                }
                attach_role_to_group(
                    neo4j_session, role_id,
                    group,
                    project_id, gcp_update_tag,
                )

            elif member.startswith('domain:'):
                dmn = member[len('domain:'):]
                domain = {
                    "id": dmn,
                    "email": dmn,
                    "name": dmn,
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_domain')
                }
                attach_role_to_domain(
                    neo4j_session, role_id,
                    domain,
                    project_id,
                    gcp_update_tag,
                )

            elif member.startswith('deleted:'):
                member = member[len('deleted:'):]
                if member.startswith('user:'):
                    usr = member[len('user:'):]
                    user = {
                        'id': usr,
                        "email": usr,
                        "name": usr.split("@")[0],
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],

                    }
                    attach_role_to_user(
                        neo4j_session, role_id, user,
                        project_id, gcp_update_tag,
                    )

                elif member.startswith('serviceAccount:'):
                    serviceAccount = {

                        'id': member[len('serviceAccount:'):],
                        'is_deleted': True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],

                    }
                    attach_role_to_service_account(
                        neo4j_session,
                        role_id, serviceAccount,
                        project_id,
                        gcp_update_tag,
                    )

                elif member.startswith('group:'):
                    grp = member[len('group:'):]
                    group = {
                        "id": grp,
                        "email": grp,
                        "name": grp.split('@')[0],
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],
                    }
                    attach_role_to_group(
                        neo4j_session, role_id,
                        group,
                        project_id, gcp_update_tag,
                    )

                elif member.startswith('domain:'):
                    dmn = member[len('domain:'):]
                    domain = {
                        "id": dmn,
                        "email": dmn,
                        "name": dmn,
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],
                    }
                    attach_role_to_domain(
                        neo4j_session, role_id,
                        domain,
                        project_id,
                        gcp_update_tag,
                    )


@timeit
def attach_role_to_user(
    neo4j_session: neo4j.Session, role_id: str, user: Dict,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (user:GCPUser{id: $UserId})
    ON CREATE SET
    user:GCPPrincipal,
    user.firstseen = timestamp()
    SET

    user.email = $UserEmail,
    user.name = $UserName,
    user.create_date = $createDate,
    user.lastupdated = $gcp_update_tag,
    user.isDeleted = $isDeleted,
    user.consolelink = $ConsoleLink
    WITH user
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (user)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH user,role
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[pr:RESOURCE]->(user)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    WITH user,role
    SET
    role.parent = $Parent,
    role.parent_id = $ParentId
    WITH user
    WHERE (NOT EXISTS(user.parent)) OR
    NOT user.parent IN ['organization', 'folder']
    SET
    user.parent = $Parent,
    user.parent_id = $ParentId
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        UserId=user['id'],
        UserEmail=user['email'],
        UserName=user['name'],
        ConsoleLink=user.get('consolelink'),
        createDate=datetime.utcnow(),
        Parent=user['parent'],
        ParentId=user['parent_id'],
        isDeleted=user.get('is_deleted', False),
        gcp_update_tag=gcp_update_tag,
        project_id=project_id,
    )


@timeit
def attach_role_to_service_account(
    neo4j_session: neo4j.Session, role_id: str,
    serviceAccount: Dict, project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (sa:GCPServiceAccount{id: $saId})
    SET
    sa.isDeleted = $isDeleted
    WITH sa
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (sa)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH sa,role
    SET
    role.parent = $Parent,
    role.parent_id = $ParentId
    WITH sa
    WHERE (NOT EXISTS(sa.parent)) OR
    NOT sa.parent IN ['organization', 'folder']
    SET
    sa.parent = $Parent,
    sa.parent_id = $ParentId
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        isDeleted=serviceAccount.get('is_deleted', False),
        Parent=serviceAccount['parent'],
        ParentId=serviceAccount['parent_id'],
        saId=serviceAccount['id'],
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_role_to_group(
    neo4j_session: neo4j.Session, role_id: str, group: Dict,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (group:GCPGroup{id: $GroupId})
    ON CREATE SET
    group:GCPPrincipal,
    group.firstseen = timestamp()
    SET
    group.email = $GroupEmail,
    group.name = $GroupName,
    group.create_date = $createDate,
    group.consolelink = $ConsoleLink,
    group.lastupdated = $gcp_update_tag,
    group.isDeleted = $isDeleted
    WITH group
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (group)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH group,role
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[pr:RESOURCE]->(group)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    WITH group,role
    SET
    role.parent = $Parent,
    role.parent_id = $ParentId
    WITH group
    WHERE (NOT EXISTS(group.parent)) OR
    NOT group.parent IN ['organization', 'folder']
    SET
    group.parent = $Parent,
    group.parent_id = $ParentId
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        GroupId=group['id'],
        GroupName=group['name'],
        createDate=datetime.utcnow(),
        GroupEmail=group['email'],
        ConsoleLink=group['consolelink'],
        Parent=group['parent'],
        ParentId=group['parent_id'],
        isDeleted=group.get('is_deleted', False),
        gcp_update_tag=gcp_update_tag,
        project_id=project_id,
    )


@timeit
def attach_role_to_domain(
    neo4j_session: neo4j.Session, role_id: str, domain: Dict,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (domain:GCPDomain{id: $DomainId})
    ON CREATE SET
    domain:GCPPrincipal,
    domain.firstseen = timestamp()
    SET
    domain.email = $DomainEmail,
    domain.name = $DomainName,
    domain.create_date = $createDate,
    domain.consolelink = $ConsoleLink,
    domain.lastupdated = $gcp_update_tag,
    domain.isDeleted = $isDeleted
    WITH domain
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (domain)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH domain,role
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[pr:RESOURCE]->(domain)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    WITH domain,role
    SET
    role.parent = $Parent,
    role.parent_id = $ParentId
    WITH domain
    WHERE (NOT EXISTS(domain.parent)) OR
    NOT domain.parent IN ['organization', 'folder']
    SET
    domain.parent = $Parent,
    domain.parent_id = $ParentId
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        DomainId=domain['id'],
        Parent=domain['parent'],
        createDate=datetime.utcnow(),
        ParentId=domain['parent_id'],
        DomainEmail=domain['email'],
        ConsoleLink=domain['consolelink'],
        DomainName=domain['name'],
        isDeleted=domain.get('is_deleted', False),
        gcp_update_tag=gcp_update_tag,
        project_id=project_id,
    )


def _set_used_state_tx(
    tx: neo4j.Transaction, project_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPRole)
    WHERE (n)<-[:ASSUME_ROLE]-() AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=True,
    )

    ingest_entity_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPPrincipal)
    WHERE ()<-[:ASSUME_ROLE]-(n) AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPPrincipal)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=False,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, iam: Resource, crm_v1: Resource, crm_v2: Resource, apikey: Resource,
    project_id: str, gcp_update_tag: int, common_job_parameters: Dict
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing IAM for project '%s', at %s.", project_id, tic)

    service_accounts_list = get_service_accounts(iam, project_id)
    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(service_accounts_list) / pageSize

        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam service_accounts {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (
            common_job_parameters.get('pagination', {}).get('iam', {})[
                'pageNo'
            ] - 1
        ) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']

        if page_end > len(service_accounts_list) or page_end == len(service_accounts_list):
            service_accounts_list = service_accounts_list[page_start:]

        else:
            has_next_page = True
            service_accounts_list = service_accounts_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    service_accounts_list = transform_service_accounts(service_accounts_list, project_id)
    load_service_accounts(neo4j_session, service_accounts_list, project_id, gcp_update_tag)

    for service_account in service_accounts_list:
        service_account_keys = get_service_account_keys(iam, project_id, service_account)
        load_service_account_keys(neo4j_session, service_account_keys, service_account['id'], gcp_update_tag)

    cleanup_service_accounts(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, service_accounts_list, gcp_update_tag,
        common_job_parameters, 'service accounts', 'GCPServiceAccount',
    )

    roles_list = []

    predefined_roles_list = get_predefined_roles(iam, project_id)
    project_custom_roles_list = get_project_custom_roles(iam, project_id)
    organization_custom_roles_list = get_organization_custom_roles(iam, crm_v1, project_id)

    predefined_roles_list = transform_roles(predefined_roles_list, project_id, 'predefined')
    project_custom_roles_list = transform_roles(project_custom_roles_list, project_id, 'custom')
    organization_custom_roles_list = transform_roles(organization_custom_roles_list, project_id, 'custom')

    roles_list.extend(predefined_roles_list)
    roles_list.extend(project_custom_roles_list)
    roles_list.extend(organization_custom_roles_list)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(roles_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam roles {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (
            common_job_parameters.get('pagination', {}).get('iam', {})[
                'pageNo'
            ] - 1
        ) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(roles_list) or page_end == len(roles_list):
            roles_list = roles_list[page_start:]

        else:
            has_next_page = True
            roles_list = roles_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_roles(neo4j_session, roles_list, project_id, gcp_update_tag)
    cleanup_roles(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, roles_list, gcp_update_tag, common_job_parameters, 'roles', 'GCPRole')

    # users = get_users(admin)

    # if common_job_parameters.get('pagination', {}).get('iam', None):
    #     pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
    #     pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
    #     totalPages = len(users) / pageSize
    #     if int(totalPages) != totalPages:
    #         totalPages = totalPages + 1

    #     totalPages = int(totalPages)
    #     if pageNo < totalPages or pageNo == totalPages:
    #         logger.info(f'pages process for iam users {pageNo}/{totalPages} pageSize is {pageSize}')

    #     page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
    #                   'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
    #     page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
    #     if page_end > len(users) or page_end == len(users):
    #         users = users[page_start:]

    #     else:
    #         has_next_page = True
    #         users = users[page_start:page_end]
    #         common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    # customer_ids = []
    # for user in users:
    #     customer_ids.append(get_customer(user.get('customerId')))

    # customer_ids = list(set(customer_ids))
    # customer_ids.sort()

    # customers = []
    # for customer_id in customer_ids:
    #     customers.append(get_customer(customer_id))

    # load_customers(neo4j_session, customers, project_id, gcp_update_tag)
    # cleanup_customers(neo4j_session, common_job_parameters)

    # load_users(neo4j_session, users, project_id, gcp_update_tag)
    # cleanup_users(neo4j_session, common_job_parameters)
    # label.sync_labels(neo4j_session, users, gcp_update_tag, common_job_parameters, 'users', 'GCPUser')

    # for customer in customers:
    #     domains = get_domains(admin, customer, project_id)
    #     load_domains(neo4j_session, domains, customer.get('id'), project_id, gcp_update_tag)

    # cleanup_domains(neo4j_session, common_job_parameters)

    # groups = get_groups(admin)

    # if common_job_parameters.get('pagination', {}).get('iam', None):
    #     pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
    #     pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
    #     totalPages = len(groups) / pageSize
    #     if int(totalPages) != totalPages:
    #         totalPages = totalPages + 1

    #     totalPages = int(totalPages)
    #     if pageNo < totalPages or pageNo == totalPages:
    #         logger.info(f'pages process for iam groups {pageNo}/{totalPages} pageSize is {pageSize}')

    #     page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
    #                   'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
    #     page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
    #     if page_end > len(groups) or page_end == len(groups):
    #         groups = groups[page_start:]

    #     else:
    #         has_next_page = True
    #         groups = groups[page_start:page_end]
    #         common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    # load_groups(neo4j_session, groups, project_id, gcp_update_tag)
    # cleanup_groups(neo4j_session, common_job_parameters)
    # label.sync_labels(neo4j_session, groups, gcp_update_tag, common_job_parameters, 'groups', 'GCPGroup')

    keys = get_apikeys_keys(apikey, project_id)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(keys) / pageSize

        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam service_accounts {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (
            common_job_parameters.get('pagination', {}).get('iam', {})[
                'pageNo'
            ] - 1
        ) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']

        if page_end > len(keys) or page_end == len(keys):
            keys = keys[page_start:]

        else:
            has_next_page = True
            keys = keys[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    api_keys = transform_api_keys(keys, project_id)
    load_api_keys(neo4j_session, api_keys, project_id, gcp_update_tag)
    cleanup_api_keys(neo4j_session, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        if not common_job_parameters.get('pagination', {}).get('iam', {}).get('hasNextPage', False):
            bindings = get_policy_bindings(crm_v1, crm_v2, project_id)
            # users_from_bindings, groups_from_bindings, domains_from_bindings = transform_bindings(bindings, project_id)
            load_bindings(neo4j_session, bindings, project_id, gcp_update_tag)
            set_used_state(neo4j_session, project_id, common_job_parameters, gcp_update_tag)
    else:
        bindings = get_policy_bindings(crm_v1, crm_v2, project_id)
        # users_from_bindings, groups_from_bindings, domains_from_bindings = transform_bindings(bindings, project_id)
        load_bindings(neo4j_session, bindings, project_id, gcp_update_tag)
        set_used_state(neo4j_session, project_id, common_job_parameters, gcp_update_tag)

    toc = time.perf_counter()
    logger.info(f"Time to process IAM: {toc - tic:0.4f} seconds")

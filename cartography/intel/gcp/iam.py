import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)


@timeit
def get_users(admin: Resource) -> List[Dict]:
    users = []
    try:
        req = admin.users().list()
        while req is not None:
            res = req.execute()
            page = res.get('users', [])
            users.extend(page)
            req = admin.users().list_next(previous_request=req, previous_response=res)
        return users
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve users due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_customer(admin: Resource, customer_id: str) -> Dict:
    try:
        req = admin.customers().get(customer=customer_id)
        return req.execute()
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve customer due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return {}
        else:
            raise


@timeit
def get_domains(admin: Resource, customer_id: str, project_id: str) -> List[Dict]:
    domains = []
    try:
        req = admin.domains().list(customer=customer_id)
        while req is not None:
            res = req.execute()
            page = res.get('domains', [])
            domains.extend(page)
        for domain in domains:
            domain["id"] = f"projects/{project_id}/domains/{domain.get('domainName',None)}"
        return domains
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve domains due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_groups(admin: Resource) -> List[Dict]:
    groups = []
    try:
        req = admin.groups().list()
        while req is not None:
            res = req.execute()
            page = res.get('groups', [])
            groups.extend(page)
            req = admin.groups().list_next(previous_request=req, previous_response=res)
        return groups
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve groups due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_service_accounts(iam: Resource, project_id: str) -> List[Dict]:
    service_accounts: List[Dict] = []
    try:
        req = iam.projects().serviceAccounts().list(name=f'projects/{project_id}')
        while req is not None:
            res = req.execute()
            page = res.get('accounts', [])
            page['id'] = res['name']
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
def transform_service_accounts(service_accounts: List[Dict]) -> List[Dict]:
    for account in service_accounts:
        account['firstName'] = account['name'].split('@')[0]

    return service_accounts


@timeit
def get_service_account_keys(iam: Resource, project_id: str, service_account: str) -> List[Dict]:
    service_keys: List[Dict] = []
    try:
        res = iam.projects().serviceAccounts().keys().list(name=service_account).execute()
        keys = res.get('keys', [])
        for key in keys:
            key['id'] = key['name'].split('/')[-1]
            key['serviceaccount'] = service_account

        service_keys.extend(keys)

        return service_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve Keys on project %s & account %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, service_account, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_roles(iam: Resource, project_id: str) -> List[Dict]:
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
                    "Could not retrieve role on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_project_roles(iam: Resource, project_id: str) -> List[Dict]:
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
                    "Could not retrieve role on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_roles(roles_list: List[Dict], project_id: str) -> List[Dict]:
    for role in roles_list:
        role['id'] = get_role_id(role['name'], project_id)

    return roles_list


@timeit
def get_role_id(role_name: str, project_id: str) -> str:
    if role_name.startswith('organizations/'):
        return role_name

    elif role_name.startswith('projects/'):
        return role_name

    elif role_name.startswith('roles/'):
        return f'projects/{project_id}/roles/{role_name}'
    return ''


@timeit
def get_policy_bindings(crm: Resource, project_id: str) -> List[Dict]:
    try:
        req = crm.projects().getIamPolicy(resource=project_id, body={'options': {'requestedPolicyVersion': 3}})
        res = req.execute()

        if res.get('bindings'):
            return res['bindings']

        return []
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve policy bindings on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


def transform_bindings(bindings: List[Dict], project_id: str) -> tuple:
    users = []
    groups = []
    domains = []

    for binding in bindings:
        for member in binding['members']:
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

    return (
        [dict(s) for s in {frozenset(d.items()) for d in users}],
        [dict(s) for s in {frozenset(d.items()) for d in groups}],
        [dict(s) for s in {frozenset(d.items()) for d in domains}],
    )


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict], project_id: str, gcp_update_tag: int,
) -> None:
    ingest_service_accounts = """
    UNWIND $service_accounts_list AS sa
    MERGE (u:GCPServiceAccount{id: sa.name})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = sa.name, u.displayname = sa.displayName,
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
        project_id=project_id,
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
    SET u.name=sa.name, u.serviceaccountid=$serviceaccount,
    u.keytype = sa.keyType, u.origin = sa.keyOrigin,
    u.algorithm = sa.keyAlgorithm, u.validbeforetime = sa.validBeforeTime,
    u.validaftertime = sa.validAfterTime, u.lastupdated = $gcp_update_tag
    WITH u, sa
    MATCH (d:GCPServiceAccount{id: sa.serviceaccount})
    MERGE (d)-[r:HAS_KEY]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_service_accounts,
        service_account_keys_list=service_account_keys,
        serviceaccount=service_account,
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
    SET u.name = d.name, u.title = d.title,
    u.description = d.description, u.deleted = d.deleted,
    u.permissions = d.includedPermissions, u.roleid = d.id,
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
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_roles_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_customers(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_customers_tx, data_list, project_id, update_tag)


@timeit
def _load_customers_tx(tx: neo4j.Transaction, customers: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    ingest_customers = """
    UNWIND $customers as cst
        MERGE (customer:GCPcustomer{id:cst.id})
        ON CREATE SET
            customer.firstseen = timestamp()
        SET
            customer.customerDomain = cst.customerDomain,
            customer.kind = cst.kind,
            customer.alternateEmail = cst.alternateEmail,
            customer.customerCreationTime = cst.customerCreationTime,
            customer.phoneNumber = cst.phoneNumber,
            customer.lastupdated = $gcp_update_tag
        WITH customer, cst
        MATCH (p:GCPProject{id: $project_id})
        MERGE (p)-[r:RESOURCE]->(customer)
        ON CREATE SET
            r.firstseen = timestamp(),
            r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_customers,
        customers=customers,
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_customers(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_customers_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_users(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_users_tx, data_list, project_id, update_tag)


@timeit
def _load_users_tx(tx: neo4j.Transaction, users: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    ingest_users = """
    UNWIND $users as usr
    MERGE (user:GCPUser{id:usr.id})
    ON CREATE SET
        user.firstseen = timestamp()
    SET
        user.id = usr.id,
        user.primaryEmail = usr.primaryEmail,
        user.isAdmin = usr.isAdmin,
        user.isDelegatedAdmin = usr.isDelegatedAdmin,
        user.agreedToTerms = usr.agreedToTerms,
        user.suspended = usr.suspended,
        user.changePasswordAtNextLogin = usr.changePasswordAtNextLogin,
        user.ipWhitelisted = usr.ipWhitelisted,
        user.fullName = usr.name.fullName,
        user.familyName = usr.name.familyName,
        user.givenName = usr.name.givenName,
        user.isMailboxSetup = usr.isMailboxSetup,
        user.customerId = usr.customerId,
        user.addresses = usr.addresses,
        user.organizations = usr.organizations,
        user.lastLoginTime = usr.lastLoginTime,
        user.suspensionReason = usr.suspensionReason,
        user.creationTime = usr.creationTime,
        user.deletionTime = usr.deletionTime,
        user.gender = usr.gender,
        user.lastupdated = $gcp_update_tag
    WITH user, usr
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(user)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_users,
        users=users,
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_users(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_users_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_groups(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_groups_tx, data_list, project_id, update_tag)


@timeit
def _load_groups_tx(tx: neo4j.Transaction, groups: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    ingest_groups = """
    UNWIND $groups as grp
    MERGE (group:GCPGroup{id:grp.id})
    ON CREATE SET
        group.firstseen = timestamp()
    SET
        group.id = grp.id,
        group.email = grp.email,
        group.adminCreated = grp.adminCreated,
        group.directMembersCount = grp.directMembersCount,
        group.lastupdated = $gcp_update_tag
    WITH group,grp
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(group)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_groups,
        groups=groups,
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_groups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_domains(
    session: neo4j.Session, data_list: List[Dict], customer_id: str, project_id: str, update_tag: int,
) -> None:
    session.write_transaction(_load_domains_tx, data_list, customer_id, project_id, update_tag)


@timeit
def _load_domains_tx(
    tx: neo4j.Transaction, domains: List[Dict], customer_id: str, project_id: str, gcp_update_tag: int,
) -> None:
    ingest_domains = """
    UNWIND $domains as dmn
    MERGE (domain:GCPDomain{id:dmn.id})
    ON CREATE SET
        domain.firstseen = timestamp()
    SET
        domain.verified = dmn.verified,
        domain.creationTime = dmn.creationTime,
        domain.isPrimary = dmn.isPrimary,
        domain.domainName = dmn.domainName,
        domain.kind = dmn.kind,
        domain.name = dmn.domainName,
        domain.lastupdated = $gcp_update_tag
    WITH domain
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(domain)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    WITH domain
    MATCH (p:GCPCustomer{id: $customer_id})
    MERGE (p)-[r:RESOURCE]->(domain)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_domains,
        domains=domains,
        project_id=project_id,
        customer_id=customer_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_domains(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_domains_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_bindings(neo4j_session: neo4j.Session, bindings: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    for binding in bindings:
        role_id = get_role_id(binding['role'], project_id)

        for member in binding['members']:
            if member.startswith('user:'):
                attach_role_to_user(
                    neo4j_session, role_id, f"projects/{project_id}/users/{member[len('user:'):]}",
                    project_id, gcp_update_tag,
                )

            elif member.startswith('serviceAccount:'):
                attach_role_to_service_account(
                    neo4j_session,
                    role_id, f"projects/{project_id}/serviceAccounts/{member[len('serviceAccount:'):]}",
                    project_id,
                    gcp_update_tag,
                )

            elif member.startswith('group:'):
                attach_role_to_group(
                    neo4j_session, role_id,
                    f"projects/{project_id}/groups/{member[len('group:'):]}",
                    project_id, gcp_update_tag,
                )

            elif member.startswith('domain:'):
                attach_role_to_domain(
                    neo4j_session, role_id,
                    f"projects/{project_id}/domains/{member[len('domain:'):]}",
                    project_id,
                    gcp_update_tag,
                )


@timeit
def attach_role_to_user(
    neo4j_session: neo4j.Session, role_id: str, user_id: str,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (user:GCPUser{id: $UserId})
    MERGE (user)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        UserId=user_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_role_to_service_account(
    neo4j_session: neo4j.Session, role_id: str,
    service_account_id: str, project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (sa:GCPServiceAccount{id: $saId})
    MERGE (sa)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        saId=service_account_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_role_to_group(
    neo4j_session: neo4j.Session, role_id: str, group_id: str,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (group:GCPGroup{id: $GroupId})
    MERGE (group)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        GroupId=group_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_role_to_domain(
    neo4j_session: neo4j.Session, role_id: str, domain_id: str,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (role:GCPRole{id: $RoleId})
    MERGE (domain:GCPDomain{id: $DomainId})
    MERGE (domain)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        DomainId=domain_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, iam: Resource, crm: Resource, admin: Resource,
    project_id: str, gcp_update_tag: int, common_job_parameters: Dict, regions: List[str],
) -> None:
    logger.info("Syncing IAM objects for project %s.", project_id)

    service_accounts_list = get_service_accounts(iam, project_id)
    service_accounts_list = transform_service_accounts(service_accounts_list)
    load_service_accounts(neo4j_session, service_accounts_list, project_id, gcp_update_tag)
    cleanup_service_accounts(neo4j_session, common_job_parameters)

    for service_account in service_accounts_list:
        service_account_keys = get_service_account_keys(iam, project_id, service_account['name'])
        load_service_account_keys(neo4j_session, service_account_keys, service_account['name'], gcp_update_tag)

    cleanup_service_account_keys(neo4j_session, common_job_parameters)

    roles_list = get_roles(iam, project_id)
    custom_roles_list = get_project_roles(iam, project_id)
    roles_list.extend(custom_roles_list)

    roles_list = transform_roles(roles_list, project_id)

    load_roles(neo4j_session, roles_list, project_id, gcp_update_tag)
    cleanup_roles(neo4j_session, common_job_parameters)

    users = get_users(admin)

    customer_ids = []
    for user in users:
        customer_ids.append(get_customer(user.get('customerId')))

    customer_ids = list(set(customer_ids))
    customer_ids.sort()

    customers = []
    for customer_id in customer_ids:
        customers.append(get_customer(customer_id))

    load_customers(neo4j_session, customers, project_id, gcp_update_tag)
    cleanup_customers(neo4j_session, common_job_parameters)

    load_users(neo4j_session, users, project_id, gcp_update_tag)
    cleanup_users(neo4j_session, common_job_parameters)

    for customer in customers:
        domains = get_domains(admin, customer, project_id)
        load_domains(neo4j_session, domains, customer.get('id'), project_id, gcp_update_tag)

    cleanup_domains(neo4j_session, common_job_parameters)

    groups = get_groups(admin)
    load_groups(neo4j_session, groups, project_id, gcp_update_tag)
    cleanup_groups(neo4j_session, common_job_parameters)

    bindings = get_policy_bindings(crm, project_id)

    # users_from_bindings, groups_from_bindings, domains_from_bindings = transform_bindings(bindings, project_id)

    load_bindings(neo4j_session, bindings, project_id, gcp_update_tag)

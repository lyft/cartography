import asyncio
import logging
import math
from datetime import datetime
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.msi import ManagedServiceIdentityClient
from cloudconsolelink.clouds.azure import AzureLinker
from msgraph import GraphServiceClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()

scopes = ['https://graph.microsoft.com/.default']


def load_tenant_users(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    iteration_size = 500
    total_items = len(data_list)
    total_iterations = math.ceil(len(data_list) / iteration_size)

    for counter in range(0, total_iterations):
        start = iteration_size * (counter)

        if (start + iteration_size) >= total_items:
            end = total_items
            paged_users = data_list[start:]

        else:
            end = start + iteration_size
            paged_users = data_list[start:end]

        session.write_transaction(_load_tenant_users_tx, tenant_id, paged_users, update_tag)

        logger.info(f"Iteration {counter + 1} of {total_iterations}. {start} - {end} - {len(paged_users)}")


def load_roles(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int, SUBSCRIPTION_ID: str) -> None:
    session.write_transaction(_load_roles_tx, tenant_id, data_list, update_tag, SUBSCRIPTION_ID)


def load_managed_identities(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_managed_identities_tx, tenant_id, data_list, update_tag)

def load_tenant_groups(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_groups_tx, tenant_id, data_list, update_tag)


def load_tenant_applications(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_applications_tx, tenant_id, data_list, update_tag)


def load_tenant_service_accounts(
    session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int,
) -> None:
    session.write_transaction(_load_tenant_service_accounts_tx, tenant_id, data_list, update_tag)


def load_tenant_domains(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_domains_tx, tenant_id, data_list, update_tag)


def set_used_state(session: neo4j.Session, tenant_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.write_transaction(_set_used_state_tx, tenant_id, common_job_parameters, update_tag)


@timeit
def get_graph_client(credentials: Credentials, tenant_id: str) -> GraphRbacManagementClient:
    client = GraphRbacManagementClient(credentials, tenant_id)
    return client


@timeit
def get_default_graph_client(credentials: Credentials) -> GraphServiceClient:
    client = GraphServiceClient(credentials, scopes)
    return client


@timeit
def get_authorization_client(credentials: Credentials, subscription_id: str) -> AuthorizationManagementClient:
    client = AuthorizationManagementClient(credentials, subscription_id)
    return client


@timeit
def get_managed_identity_client(credentials: Credentials, subscription_id: str) -> ManagedServiceIdentityClient:
    client = ManagedServiceIdentityClient(credentials, subscription_id)
    return client

@timeit
def list_tenant_users(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        users = client.users.list()

        users = transform_users(client.users.list(), tenant_id)

        return users

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant users - {e}")
        return []


def transform_users(users_list: List[Dict], tenant_id: str) -> List[Dict]:
    users: List[Dict] = []

    # User properties - https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    for user in users_list:
        usr = {
            'id': f"tenants/{tenant_id}/users/{user.object_id}",
            'consolelink': azure_console_link.get_console_link(id=user.object_id, iam_entity_type='user'),
            'object_id': user.object_id,
            'user_principal_name': user.user_principal_name,
            'email': user.mail,
            'name': user.display_name,
            'given_name': user.given_name,
            'surname': user.surname,
            'user_type': user.user_type,
            'object_type': user.object_type,
            'mail_nickname': user.mail_nickname,
            'account_enabled': user.account_enabled,
            'usage_location': user.usage_location,
            'account_enabled': user.account_enabled,
            'deletion_timestamp': user.deletion_timestamp,
            'create_date': user.additional_properties['createdDateTime'],
            'company_name': user.additional_properties['companyName'],
            'refresh_tokens_valid_from': user.additional_properties['refreshTokensValidFromDateTime'],
            'mobile': user.additional_properties['mobile'],
        }
        users.append(usr)

    return users


def transform_user(user: Dict, tenant_id: str) -> Dict:
    # User properties - https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    return {
        'id': f"tenants/{tenant_id}/users/{user.object_id}",
        'consolelink': azure_console_link.get_console_link(id=user.object_id, iam_entity_type='user'),
        'object_id': user.object_id,
        'user_principal_name': user.user_principal_name,
        'email': user.mail,
        'name': user.display_name,
        'given_name': user.given_name,
        'surname': user.surname,
        'user_type': user.user_type,
        'object_type': user.object_type,
        'mail_nickname': user.mail_nickname,
        'account_enabled': user.account_enabled,
        'usage_location': user.usage_location,
        'account_enabled': user.account_enabled,
        'deletion_timestamp': user.deletion_timestamp,
        'create_date': user.additional_properties['createdDateTime'],
        'company_name': user.additional_properties['companyName'],
        'refresh_tokens_valid_from': user.additional_properties['refreshTokensValidFromDateTime'],
        'mobile': user.additional_properties['mobile'],
    }


def _load_tenant_users_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_users_list: List[Dict], update_tag: int,
) -> None:
    ingest_user = """
    UNWIND $tenant_users_list AS user
    MERGE (i:AzureUser{id: user.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.consolelink =user.consolelink,
    i.object_id =user.object_id,
    i.user_principal_name =user.user_principal_name,
    i.email =user.email,
    i.name =user.name,
    i.given_name =user.given_name,
    i.surname =user.surname,
    i.user_type =user.user_type,
    i.object_type =user.object_type,
    i.mail_nickname =user.mail_nickname,
    i.account_enabled =user.account_enabled,
    i.usage_location =user.usage_location,
    i.account_enabled =user.account_enabled,
    i.deletion_timestamp =user.deletion_timestamp,
    i.create_date =user.create_date,
    i.company_name =user.company_name,
    i.refresh_tokens_valid_from =user.refresh_tokens_valid_from,
    i.mobile =user.mobile,
    i.region = $region
    SET i.lastupdated = $update_tag,
    i.consolelink =user.consolelink,
    i.user_principal_name =user.user_principal_name,
    i.name =user.name,
    i.given_name =user.given_name,
    i.surname =user.surname,
    i.mail_nickname =user.mail_nickname,
    i.account_enabled =user.account_enabled,
    i.usage_location =user.usage_location,
    i.account_enabled =user.account_enabled,
    i.deletion_timestamp =user.deletion_timestamp,
    i.create_date =user.create_date,
    i.company_name =user.company_name,
    i.refresh_tokens_valid_from =user.refresh_tokens_valid_from,
    i.mobile =user.mobile,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_user,
        region="global",
        tenant_users_list=tenant_users_list,
        createDate=datetime.utcnow(),
        tenant_id=tenant_id,
        update_tag=update_tag,
    )


def cleanup_tenant_users(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_users_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_users(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_users_list = list_tenant_users(client, tenant_id)

    load_tenant_users(neo4j_session, tenant_id, tenant_users_list, update_tag)
    cleanup_tenant_users(neo4j_session, common_job_parameters)


@timeit
def get_tenant_groups_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_groups_list = list(map(lambda x: x.as_dict(), client.groups.list()))

        for group in tenant_groups_list:
            group['id'] = f"tenants/{tenant_id}/Groups/{group.get('object_id', None)}"
            group['consolelink'] = azure_console_link.get_console_link(iam_entity_type='group', id=group['object_id'])

        return tenant_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant groups - {e}")
        return []


def _load_tenant_groups_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_group = """
    UNWIND $tenant_groups_list AS group
    MERGE (i:AzureGroup{id: group.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id=group.object_id,
    i.region = $region,
    i.create_date = $createDate,
    i.name = group.display_name,
    i.visibility = group.visibility,
    i.classification = group.classification,
    i.createdDateTime = group.createdDateTime,
    i.consolelink = group.consolelink,
    i.securityEnabled = group.security_enabled
    SET i.lastupdated = $update_tag,
    i.mail = group.mail
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_group,
        region="global",
        tenant_groups_list=tenant_groups_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


async def get_group_members(credentials: Credentials, group_id: str):
    client: GraphServiceClient = get_default_graph_client(credentials.default_graph_credentials)
    members_data = []
    try:
        members = await client.groups.by_group_id(group_id.split("/")[-1]).members.get()

        if members and members.value:
            for member in members.value:
                members_data.append({
                    "id": member.id,
                    "display_name": member.display_name,
                    "mail": member.mail,
                    "group_id": group_id,
                })
    except Exception as e:
        logger.warning(f"error to get members of group {group_id} - {e}")
    return members_data


@timeit
def load_group_memberships(neo4j_session: neo4j.Session, memberships: List[Dict], update_tag: int) -> None:
    neo4j_session.write_transaction(_load_group_memberships_tx, memberships, update_tag)


@timeit
def _load_group_memberships_tx(tx: neo4j.Transaction, memberships: List[Dict], update_tag: int) -> None:
    ingest_memberships = """
    UNWIND $memberships AS membership
        MATCH (p:AzureGroup{id: membership.group_id})
        MATCH (pr:AzurePrincipal{object_id: membership.id})
        WITH p,pr
        MERGE (pr)-[r:MEMBER_AZURE_GROUP]->(p)
        ON CREATE SET
                r.firstseen = timestamp()
        SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_memberships,
        memberships=memberships,
        update_tag=update_tag,
    )


def cleanup_tenant_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_graph_client(credentials.aad_graph_credentials, tenant_id)
    tenant_groups_list = get_tenant_groups_list(client, tenant_id)

    load_tenant_groups(neo4j_session, tenant_id, tenant_groups_list, update_tag)
    for group in tenant_groups_list:
        memberships = asyncio.run(get_group_members(credentials, group["id"]))
        load_group_memberships(neo4j_session, memberships, update_tag)

    cleanup_tenant_groups(neo4j_session, common_job_parameters)


@timeit
def get_tenant_applications_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_applications_list = list(map(lambda x: x.as_dict(), client.applications.list()))

        for app in tenant_applications_list:
            app['id'] = f"tenants/{tenant_id}/Applications/{app.get('object_id', None)}"
            app['consolelink'] = azure_console_link.get_console_link(iam_entity_type='application', id=app['app_id'])

        return tenant_applications_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant applications - {e}")
        return []


def _load_tenant_applications_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_applications_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND $tenant_applications_list AS app
    MERGE (i:AzureApplication{id: app.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id=app.object_id,
    i.region = $region,
    i.create_date = $createDate,
    i.name = app.display_name,
    i.consolelink = app.consolelink,
    i.publisherDomain = app.publisher_domain
    SET i.lastupdated = $update_tag,
    i.signInAudience = app.sign_in_audience
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_app,
        region="global",
        tenant_applications_list=tenant_applications_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


def cleanup_tenant_applications(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_applications_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_applications(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_applications_list = get_tenant_applications_list(client, tenant_id)

    load_tenant_applications(neo4j_session, tenant_id, tenant_applications_list, update_tag)
    cleanup_tenant_applications(neo4j_session, common_job_parameters)


@timeit
def get_tenant_service_accounts_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_service_accounts_list = list(
            map(lambda x: x.as_dict(), client.service_principals.list()),
        )

        for account in tenant_service_accounts_list:
            account['id'] = f"tenants/{tenant_id}/ServiceAccounts/{account.get('object_id', None)}"
            account['consolelink'] = azure_console_link.get_console_link(
                id=account['object_id'],
                app_id=account['app_id'], iam_entity_type='service_principal',
            )

        return tenant_service_accounts_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant service accounts - {e}")
        return []


def _load_tenant_service_accounts_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_service_accounts_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND $tenant_service_accounts_list AS service
    MERGE (i:AzureServiceAccount{id: service.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.name = service.display_name,
    i.consolelink = service.consolelink,
    i.region = $region,
    i.create_date = $createDate,
    i.object_id=service.object_id,
    i.accountEnabled = service.account_enabled,
    i.servicePrincipalType = service.service_principal_type
    SET i.lastupdated = $update_tag,
    i.signInAudience = service.signInAudience
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_app,
        region="global",
        tenant_service_accounts_list=tenant_service_accounts_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


def cleanup_tenant_service_accounts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_service_accounts_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_service_accounts(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_service_accounts_list = get_tenant_service_accounts_list(client, tenant_id)

    load_tenant_service_accounts(neo4j_session, tenant_id, tenant_service_accounts_list, update_tag)
    cleanup_tenant_service_accounts(neo4j_session, common_job_parameters)


@timeit
def get_tenant_domains_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_domains_list = list(map(lambda x: x.as_dict(), client.domains.list()))

        for domain in tenant_domains_list:
            domain["id"] = f"tenants/{tenant_id}/domains/{domain.get('name', None)}"
            domain['consolelink'] = azure_console_link.get_console_link(id=domain['name'], iam_entity_type='domain')

        return tenant_domains_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant domains - {e}")
        return []


def _load_tenant_domains_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_domains_list: List[Dict], update_tag: int,
) -> None:
    ingest_domain = """
    UNWIND $tenant_domains_list AS domain
    MERGE (i:AzureDomain{id: domain.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.isRoot = domain.isRoot,
    i.consolelink = domain.consolelink,
    i.region = $region,
    i.create_date = $createDate,
    i.name = domain.name,
    i.isInitial = domain.isInitial
    SET i.lastupdated = $update_tag,
    i.authenticationType = domain.authentication_type,
    i.availabilityStatus = domain.availabilityStatus
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_domain,
        region="global",
        tenant_domains_list=tenant_domains_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


def cleanup_tenant_domains(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_domains_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_domains(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_domains_list = get_tenant_domains_list(client, tenant_id)

    load_tenant_domains(neo4j_session, tenant_id, tenant_domains_list, update_tag)
    cleanup_tenant_domains(neo4j_session, common_job_parameters)


@timeit
def get_roles_list(client: AuthorizationManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        role_assignments_list = list(
            map(lambda x: x.as_dict(), client.role_assignments.list()),
        )

        roles_list = []
        for role_assignment in role_assignments_list:
            role_in_roles_list = False
            for role in roles_list:
                if role['id'] == role_assignment["role_definition_id"]:
                    role['principal_ids'].append(role_assignment['principal_id'])
                    role_in_roles_list = True
                    break

            if not role_in_roles_list:
                role = {}
                result = client.role_definitions.get_by_id(role_assignment["role_definition_id"], raw=True)
                result = result.response.json()
                role['name'] = result.get('name', '')
                role['id'] = role_assignment["role_definition_id"]
                role['principal_ids'] = [role_assignment['principal_id']]
                role['type'] = result.get('properties', {}).get('type')
                role['roleName'] = result.get('properties', {}).get('roleName', '')
                role['consolelink'] = azure_console_link.get_console_link(
                    id=role_assignment['role_definition_id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                role['permissions'] = []
                for permission in result.get('properties', {}).get('permissions', []):
                    for action in permission.get('actions', []):
                        role['permissions'].append(action)
                    for data_action in permission.get('dataActions', []):
                        role['permissions'].append(data_action)
                role['permissions'] = list(set(role['permissions']))
                roles_list.append(role)
        return roles_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving roles - {e}")
        return []


@timeit
def get_managed_identity_list(client: ManagedServiceIdentityClient, subscription_id: str, common_job_parameters: Dict) -> List[Dict]:
    try:
        managed_identity_list = list(
            map(lambda x: x.as_dict(), client.user_assigned_identities.list_by_subscription()),
        )

        for managed_identity in managed_identity_list:
            managed_identity['consolelink'] = azure_console_link.get_console_link(
                id=managed_identity['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
        return managed_identity_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving managed identity - {e}")
        return []

def _load_roles_tx(
    tx: neo4j.Transaction, tenant_id: str, roles_list: List[Dict], update_tag: int, SUBSCRIPTION_ID: str,
) -> None:
    ingest_role = """
    UNWIND $roles_list AS role
    MERGE (i:AzureRole{id: role.id})
    ON CREATE SET i.firstseen = timestamp(),
    i.name = role.name,
    i.consolelink = role.consolelink,
    i.region = $region,
    i.create_date = $createDate,
    i.type = role.type
    SET i.lastupdated = $update_tag,
    i.roleName = role.roleName,
    i.permissions = role.permissions
    WITH i,role
    MATCH (t:AzureTenant{id: $tenant_id})
    MERGE (t)-[tr:RESOURCE]->(i)
    ON CREATE SET tr.firstseen = timestamp()
    SET tr.lastupdated = $update_tag
    WITH i,role
    MATCH (sub:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (sub)<-[sr:HAS_ACCESS]-(i)
    ON CREATE SET sr.firstseen = timestamp()
    SET sr.lastupdated = $update_tag
    """

    tx.run(
        ingest_role,
        region="global",
        roles_list=roles_list,
        update_tag=update_tag,
        createDate=datetime.utcnow(),
        tenant_id=tenant_id,
        SUBSCRIPTION_ID=SUBSCRIPTION_ID,
    )

    attach_role = """
    UNWIND $principal_ids AS principal_id
    MATCH (principal:AzurePrincipal{object_id: principal_id})
    WITH principal
    MATCH (i:AzureRole{id: $role})
    WITH i,principal
    MERGE (principal)-[r:ASSUME_ROLE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for role in roles_list:
        tx.run(
            attach_role,
            role=role['id'],
            principal_ids=role['principal_ids'],
            update_tag=update_tag,
        )


def _load_managed_identities_tx(
    tx: neo4j.Transaction, tenant_id: str, managed_identity_list: List[Dict], update_tag: int,
) -> None:
    ingest_managed_identity = """
    UNWIND $managed_identity_list AS managed_identity
    MERGE (i:AzureManagedIdentity{id: managed_identity.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.name = managed_identity.name,
    i.consolelink = managed_identity.consolelink,
    i.location = managed_identity.location,
    i.type = managed_identity.type,
    i.object_id = managed_identity.principal_id,
    i.principal_id = managed_identity.principal_id,
    i.client_id = managed_identity.client_id
    SET i.lastupdated = $update_tag
    WITH i
    MATCH (t:AzureTenant{id: $tenant_id})
    MERGE (t)-[tr:RESOURCE]->(i)
    ON CREATE SET tr.firstseen = timestamp()
    SET tr.lastupdated = $update_tag
    """

    tx.run(
        ingest_managed_identity,
        managed_identity_list=managed_identity_list,
        update_tag=update_tag,
        tenant_id=tenant_id,
    )

def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_roles_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_managed_identities(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_managed_identity_cleanup.json', neo4j_session, common_job_parameters)

def sync_roles(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_authorization_client(credentials.arm_credentials, credentials.subscription_id)
    roles_list = get_roles_list(client, common_job_parameters)
    load_roles(neo4j_session, tenant_id, roles_list, update_tag, credentials.subscription_id)
    cleanup_roles(neo4j_session, common_job_parameters)


def sync_managed_identity(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_managed_identity_client(credentials.arm_credentials, credentials.subscription_id)
    managed_identity_list = get_managed_identity_list(client, credentials.subscription_id, common_job_parameters)
    load_managed_identities(neo4j_session, tenant_id, managed_identity_list, update_tag)
    cleanup_managed_identities(neo4j_session, common_job_parameters)


def _set_used_state_tx(
    tx: neo4j.Transaction, tenant_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:AzureTenant{id: $AZURE_TENANT_ID})-[r:RESOURCE]->(n:AzureRole)<-[:ASSUME_ROLE]-(p:AzurePrincipal)
    WHERE n.lastupdated = $update_tag
    SET n.isUsed = $isUsed,
    p.isUsed = $isUsed
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AZURE_TENANT_ID=tenant_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:AzureTenant{id: $AZURE_TENANT_ID})-[r:RESOURCE]->(n)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = $update_tag
    AND labels(n) IN [['AzureUser'], ['AzureGroup'], ['AzureServiceAccount'], ['AzureRole']]
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AZURE_TENANT_ID=tenant_id,
        isUsed=False,
    )

@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM for Tenant '%s'.", tenant_id)

    common_job_parameters['AZURE_TENANT_ID'] = tenant_id

    try:
        sync_tenant_users(
            neo4j_session, credentials.aad_graph_credentials, tenant_id,
            update_tag, common_job_parameters,
        )
        sync_tenant_groups(
            neo4j_session, credentials, tenant_id,
            update_tag, common_job_parameters,
        )
        sync_tenant_applications(
            neo4j_session, credentials.aad_graph_credentials,
            tenant_id, update_tag, common_job_parameters,
        )
        sync_tenant_service_accounts(
            neo4j_session, credentials.aad_graph_credentials,
            tenant_id, update_tag, common_job_parameters,
        )
        sync_tenant_domains(neo4j_session, credentials.aad_graph_credentials, tenant_id, update_tag, common_job_parameters)
        sync_managed_identity(
            neo4j_session, credentials, tenant_id, update_tag, common_job_parameters,
        )

        sync_roles(
            neo4j_session, credentials, tenant_id, update_tag, common_job_parameters,
        )
        set_used_state(neo4j_session, tenant_id, common_job_parameters, update_tag)

    except Exception as ex:
        logger.error(f'exception from IAM - {ex}', exc_info=True, stack_info=True)

import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from cloudconsolelink.clouds.azure import AzureLinker
from datetime import datetime

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_tenant_users(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_users_tx, tenant_id, data_list, update_tag)


def load_roles(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_roles_tx, tenant_id, data_list, update_tag)


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
def get_authorization_client(credentials: Credentials, subscription_id: str) -> AuthorizationManagementClient:
    client = AuthorizationManagementClient(credentials, subscription_id)
    return client


@timeit
def get_tenant_users_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_users_list = list(
            map(lambda x: x.as_dict(), client.users.list()),
        )

        for user in tenant_users_list:
            user['id'] = f"tenants/{tenant_id}/users/{user.get('object_id',None)}"
            user['consolelink'] = azure_console_link.get_console_link(id=user['object_id'], iam_entity_type='user')

        return tenant_users_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant users - {e}")
        return []


def _load_tenant_users_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_users_list: List[Dict], update_tag: int,
) -> None:
    ingest_user = """
    UNWIND {tenant_users_list} AS user
    MERGE (i:AzureUser{id: user.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id=user.object_id,
    i.name = user.display_name,
    i.region = {region},
    i.create_date = {createDate},
    i.given_name = user.given_name,
    i.surname = user.surname,
    i.user_type = user.user_type,
    i.consolelink = user.consolelink,
    i.mobile = user.mobile
    SET i.lastupdated = {update_tag},
    i.account_enabled = user.account_enabled,
    i.refreshTokensValidFromDateTime = user.refreshTokensValidFromDateTime,
    i.user_principal_name = user.user_principal_name
    WITH i
    MATCH (owner:AzureTenant{id: {tenant_id}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
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
    tenant_users_list = get_tenant_users_list(client, tenant_id)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(tenant_users_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam users {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(tenant_users_list) or page_end == len(tenant_users_list):
            tenant_users_list = tenant_users_list[page_start:]
        else:
            has_next_page = True
            tenant_users_list = tenant_users_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_tenant_users(neo4j_session, tenant_id, tenant_users_list, update_tag)
    cleanup_tenant_users(neo4j_session, common_job_parameters)


@timeit
def get_tenant_groups_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_groups_list = list(map(lambda x: x.as_dict(), client.groups.list()))

        for group in tenant_groups_list:
            group['id'] = f"tenants/{tenant_id}/Groups/{group.get('object_id',None)}"
            group['consolelink'] = azure_console_link.get_console_link(iam_entity_type='group', id=group['object_id'])

        return tenant_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant groups - {e}")
        return []


def _load_tenant_groups_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_group = """
    UNWIND {tenant_groups_list} AS group
    MERGE (i:AzureGroup{id: group.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id=group.object_id,
    i.region = {region},
    i.create_date = {createDate},
    i.name = group.display_name,
    i.visibility = group.visibility,
    i.classification = group.classification,
    i.createdDateTime = group.createdDateTime,
    i.consolelink = group.consolelink,
    i.securityEnabled = group.security_enabled
    SET i.lastupdated = {update_tag},
    i.mail = group.mail
    WITH i
    MATCH (owner:AzureTenant{id: {tenant_id}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_group,
        region="global",
        tenant_groups_list=tenant_groups_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


def cleanup_tenant_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_tenant_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_groups_list = get_tenant_groups_list(client, tenant_id)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(tenant_groups_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam groups {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(tenant_groups_list) or page_end == len(tenant_groups_list):
            tenant_groups_list = tenant_groups_list[page_start:]
        else:
            has_next_page = True
            tenant_groups_list = tenant_groups_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_tenant_groups(neo4j_session, tenant_id, tenant_groups_list, update_tag)
    cleanup_tenant_groups(neo4j_session, common_job_parameters)


@timeit
def get_tenant_applications_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_applications_list = list(map(lambda x: x.as_dict(), client.applications.list()))

        for app in tenant_applications_list:
            app['id'] = f"tenants/{tenant_id}/Applications/{app.get('object_id',None)}"
            app['consolelink'] = azure_console_link.get_console_link(iam_entity_type='application', id=app['app_id'])

        return tenant_applications_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant applications - {e}")
        return []


def _load_tenant_applications_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_applications_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND {tenant_applications_list} AS app
    MERGE (i:AzureApplication{id: app.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id=app.object_id,
    i.region = {region},
    i.create_date = {createDate},
    i.name = app.display_name,
    i.consolelink = app.consolelink,
    i.publisherDomain = app.publisher_domain
    SET i.lastupdated = {update_tag},
    i.signInAudience = app.sign_in_audience
    WITH i
    MATCH (owner:AzureTenant{id: {tenant_id}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
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
    common_job_parameters: Dict
) -> None:
    client = get_graph_client(credentials, tenant_id)
    tenant_applications_list = get_tenant_applications_list(client, tenant_id)

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(tenant_applications_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam applications {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(tenant_applications_list) or page_end == len(tenant_applications_list):
            tenant_applications_list = tenant_applications_list[page_start:]
        else:
            has_next_page = True
            tenant_applications_list = tenant_applications_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_tenant_applications(neo4j_session, tenant_id, tenant_applications_list, update_tag)
    cleanup_tenant_applications(neo4j_session, common_job_parameters)


@timeit
def get_tenant_service_accounts_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_service_accounts_list = list(
            map(lambda x: x.as_dict(), client.service_principals.list()),
        )

        for account in tenant_service_accounts_list:
            account['id'] = f"tenants/{tenant_id}/ServiceAccounts/{account.get('object_id',None)}"

        return tenant_service_accounts_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant service accounts - {e}")
        return []


def _load_tenant_service_accounts_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_service_accounts_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND {tenant_service_accounts_list} AS service
    MERGE (i:AzureServiceAccount{id: service.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.name = service.display_name,
    i.region = {region},
    i.create_date = {createDate},
    i.object_id=service.object_id,
    i.accountEnabled = service.account_enabled,
    i.servicePrincipalType = service.service_principal_type
    SET i.lastupdated = {update_tag},
    i.signInAudience = service.signInAudience
    WITH i
    MATCH (owner:AzureTenant{id: {tenant_id}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
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

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(tenant_service_accounts_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam service_accounts {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(tenant_service_accounts_list) or page_end == len(tenant_service_accounts_list):
            tenant_service_accounts_list = tenant_service_accounts_list[page_start:]
        else:
            has_next_page = True
            tenant_service_accounts_list = tenant_service_accounts_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_tenant_service_accounts(neo4j_session, tenant_id, tenant_service_accounts_list, update_tag)
    cleanup_tenant_service_accounts(neo4j_session, common_job_parameters)


@timeit
def get_tenant_domains_list(client: GraphRbacManagementClient, tenant_id: str) -> List[Dict]:
    try:
        tenant_domains_list = list(map(lambda x: x.as_dict(), client.domains.list()))

        for domain in tenant_domains_list:
            domain["id"] = f"tenants/{tenant_id}/domains/{domain.get('name',None)}"

        return tenant_domains_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant domains - {e}")
        return []


def _load_tenant_domains_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_domains_list: List[Dict], update_tag: int,
) -> None:
    ingest_domain = """
    UNWIND {tenant_domains_list} AS domain
    MERGE (i:AzureDomain{id: domain.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.isRoot = domain.isRoot,
    i.region = {region},
    i.create_date = {createDate},
    i.name = domain.name,
    i.isInitial = domain.isInitial
    SET i.lastupdated = {update_tag},
    i.authenticationType = domain.authentication_type,
    i.availabilityStatus = domain.availabilityStatus
    WITH i
    MATCH (owner:AzureTenant{id: {tenant_id}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
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

    if common_job_parameters.get('pagination', {}).get('iam', None):
        pageNo = common_job_parameters.get("pagination", {}).get("iam", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("iam", None)["pageSize"]
        totalPages = len(tenant_domains_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for iam domains {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('iam', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('iam', {})['pageSize']
        if page_end > len(tenant_domains_list) or page_end == len(tenant_domains_list):
            tenant_domains_list = tenant_domains_list[page_start:]
        else:
            has_next_page = True
            tenant_domains_list = tenant_domains_list[page_start:page_end]
            common_job_parameters['pagination']['iam']['hasNextPage'] = has_next_page

    load_tenant_domains(neo4j_session, tenant_id, tenant_domains_list, update_tag)
    cleanup_tenant_domains(neo4j_session, common_job_parameters)


@timeit
def get_roles_list(client: AuthorizationManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        roles_list = list(
            map(lambda x: x.as_dict(), client.role_assignments.list()),
        )

        for role in roles_list:
            result = client.role_definitions.get_by_id(role["role_definition_id"], raw=True)
            result = result.response.json()
            role['roleName'] = result.get('properties', {}).get('roleName', '')
            role['consolelink'] = azure_console_link.get_console_link(
                id=role['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            role['permissions'] = []
            for permission in result.get('properties', {}).get('permissions', []):
                for action in permission.get('actions', []):
                    role['permissions'].append(action)
                for data_action in permission.get('dataActions', []):
                    role['permissions'].append(data_action)
            role['permissions'] = list(set(role['permissions']))
        return roles_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving roles - {e}")
        return []


def _load_roles_tx(
    tx: neo4j.Transaction, tenant_id: str, roles_list: List[Dict], update_tag: int,
) -> None:
    ingest_role = """
    UNWIND {roles_list} AS role
    MERGE (i:AzureRole{id: role.id})
    ON CREATE SET i.firstseen = timestamp(),
    i.name = role.name,
    i.consolelink = role.consolelink,
    i.region = {region},
    i.create_date = {createDate},
    i.type = role.type
    SET i.lastupdated = {update_tag},
    i.roleName = role.roleName,
    i.permissions = role.permissions
    WITH i,role
    MATCH (principal:AzurePrincipal) where principal.object_id = role.principal_id
    MERGE (principal)-[r:ASSUME_ROLE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    WITH i
    MATCH (t:AzureTenant{id: {tenant_id}})
    MERGE (t)-[tr:RESOURCE]->(i)
    ON CREATE SET tr.firstseen = timestamp()
    SET tr.lastupdated = {update_tag}
    """

    tx.run(
        ingest_role,
        region="global",
        roles_list=roles_list,
        update_tag=update_tag,
        createDate=datetime.utcnow(),
        tenant_id=tenant_id,
    )


def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_roles_cleanup.json', neo4j_session, common_job_parameters)


def sync_roles(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict
) -> None:
    client = get_authorization_client(credentials.arm_credentials, credentials.subscription_id)
    roles_list = get_roles_list(client, common_job_parameters)
    load_roles(neo4j_session, tenant_id, roles_list, update_tag)
    cleanup_roles(neo4j_session, common_job_parameters)


def _set_used_state_tx(
    tx: neo4j.Transaction, tenant_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: {WORKSPACE_ID}})-[:OWNER]->
    (:AzureTenant{id: {AZURE_TENANT_ID}})-[r:RESOURCE]->(n:AzureRole)<-[:ASSUME_ROLE]-(p:AzurePrincipal)
    WHERE n.lastupdated = {update_tag}
    SET n.isUsed = {isUsed},
    p.isUsed = {isUsed}
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AZURE_TENANT_ID=tenant_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: {WORKSPACE_ID}})-[:OWNER]->
    (:AzureTenant{id: {AZURE_TENANT_ID}})-[r:RESOURCE]->(n)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = {update_tag}
    AND labels(n) IN [['AzureUser'], ['AzureGroup'], ['AzureServiceAccount'], ['AzureRole']]
    SET n.isUsed = {isUsed}
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
        sync_tenant_users(neo4j_session, credentials.aad_graph_credentials, tenant_id,
                          update_tag, common_job_parameters)
        sync_tenant_groups(neo4j_session, credentials.aad_graph_credentials, tenant_id,
                           update_tag, common_job_parameters)
        sync_tenant_applications(
            neo4j_session, credentials.aad_graph_credentials,
            tenant_id, update_tag, common_job_parameters)
        sync_tenant_service_accounts(
            neo4j_session, credentials.aad_graph_credentials,
            tenant_id, update_tag, common_job_parameters,
        )
        sync_tenant_domains(neo4j_session, credentials.aad_graph_credentials, tenant_id, update_tag, common_job_parameters)
        if common_job_parameters.get('pagination', {}).get('iam', None):
            if not common_job_parameters.get('pagination', {}).get('iam', {}).get('hasNextPage', False):
                sync_roles(
                    neo4j_session, credentials, tenant_id, update_tag, common_job_parameters
                )
                set_used_state(neo4j_session, tenant_id, common_job_parameters, update_tag)
        else:
            sync_roles(
                neo4j_session, credentials, tenant_id, update_tag, common_job_parameters
            )
            set_used_state(neo4j_session, tenant_id, common_job_parameters, update_tag)

    except Exception as ex:
        print(f'exception from IAM - {ex}')

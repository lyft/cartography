# Okta intel module
import json
import logging
import os

from okta import AppInstanceClient
from okta import FactorsClient
from okta import UserGroupsClient
from okta import UsersClient
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError
from okta.framework.PagedResults import PagedResults
from okta.models.usergroup import UserGroup

from cartography.config import Config
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

OKTA_API_KEY = os.environ.get('CREDENTIALS_OKTA_API_KEY')


def _create_user_client(okta_org):
    """
    Create Okta User Client
    :param okta_org: Okta organization name
    :return: Instance of UsersClient
    """
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_client = UsersClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=OKTA_API_KEY,
    )

    return user_client


def _create_group_client(okta_org):
    """
    Create Okta UserGroupsClient
    :param okta_org: Okta organization name
    :return: Instance of UserGroupsClient
    """
    usergroups_client = UserGroupsClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=OKTA_API_KEY,
    )

    return usergroups_client


def _create_application_client(okta_org):
    """
    Create Okta AppInstanceClient
    :param okta_org: Okta organization name
    :return: Instance of AppInstanceClient
    """
    app_client = AppInstanceClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=OKTA_API_KEY,
    )

    return app_client


def _create_factor_client(okta_org):
    """
    Create Okta FactorsClient
    :param okta_org: Okta organization name
    :return: Instance of FactorsClient
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/FactorsClient.py
    factor_client = FactorsClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=OKTA_API_KEY,
    )

    return factor_client


def _create_api_client(okta_org, path_name):
    """
    Create Okta ApiClient
    :param okta_org: Okta organization name
    :param path_name: API Path
    :return: Instance of ApiClient
    """
    api_client = ApiClient(
        base_url=f"https://{okta_org}.okta.com/",
        pathname=path_name,
        api_token=OKTA_API_KEY,
    )

    return api_client


def _get_okta_users(user_client):
    """
    Get Okta users from Okta server
    :param user_client: user client
    :return: Array of dictionary containing user properties
    """
    user_list = []
    paged_users = user_client.get_paged_users()
    while True:
        for current_user in paged_users.result:
            user_props = transform_okta_user(current_user)
            user_list.append(user_props)
        if not paged_users.is_last_page():
            # Keep on fetching pages of users until the last page
            paged_users = user_client.get_paged_users(url=paged_users.next_url)
        else:
            break

    return user_list


def transform_okta_user(okta_user):
    """
    Transform okta user data
    :param okta_user: okta user object
    :return: Dictionary container user properties for ingestion
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props = {}
    user_props["first_name"] = okta_user.profile.firstName
    user_props["last_name"] = okta_user.profile.lastName
    user_props["login"] = okta_user.profile.login
    user_props["email"] = okta_user.profile.email
    user_props["second_email"] = okta_user.profile.secondEmail
    user_props["mobile_phone"] = okta_user.profile.mobilePhone

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
    user_props["id"] = okta_user.id
    user_props["created"] = okta_user.created.strftime("%m/%d/%Y, %H:%M:%S")
    if okta_user.activated:
        user_props["activated"] = okta_user.activated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["activated"] = None

    if okta_user.statusChanged:
        user_props["status_changed"] = okta_user.statusChanged.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["status_changed"] = None

    if okta_user.lastLogin:
        user_props["last_login"] = okta_user.lastLogin.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["last_login"] = None

    if okta_user.lastUpdated:
        user_props["okta_last_updated"] = okta_user.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["okta_last_updated"] = None

    if okta_user.passwordChanged:
        user_props["password_changed"] = okta_user.passwordChanged.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        user_props["password_changed"] = None

    if okta_user.transitioningToStatus:
        user_props["transition_to_status"] = okta_user.transitioningToStatus
    else:
        user_props["transition_to_status"] = None

    return user_props


def _load_okta_users(neo4j_session, okta_org_id, user_list, okta_update_tag):
    """
    Load Okta user information into the graph
    :param neo4j_session: session with neo4j server
    :param okta_org_id: oktat organization id
    :param user_list: list of users
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest_statement = """
    MATCH (org:OktaOrganization{id: {ORG_ID}})
    WITH org
    UNWIND {USER_LIST} as user_data
    MERGE (new_user:OktaUser{id: user_data.id})
    ON CREATE SET new_user.firstseen = timestamp()
    SET new_user.first_name = user_data.first_name,
    new_user.last_name = user_data.last_name,
    new_user.login = user_data.login,
    new_user.email = user_data.email,
    new_user.second_email = user_data.second_email,
    new_user.mobile_phone = user_data.mobile_phone,
    new_user.created = user_data.created,
    new_user.activated = user_data.activated,
    new_user.status_changed = user_data.status_changed,
    new_user.last_login = user_data.last_login,
    new_user.okta_last_updated = user_data.okta_last_updated,
    new_user.password_changed = user_data.password_changed,
    new_user.transition_to_status = user_data.transition_to_status,
    new_user.lastupdated = {okta_update_tag}
    WITH new_user, org
    MERGE (org)-[org_r:RESOURCE]->(new_user)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = {okta_update_tag}
    WITH new_user
    MERGE (h:Human{email: new_user.email})
    ON CREATE SET new_user.firstseen = timestamp()
    SET h.lastupdated = {okta_update_tag}
    MERGE (h)-[r:IDENTITY_OKTA]->(new_user)
    ON CREATE SET new_user.firstseen = timestamp()
    SET h.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        ORG_ID=okta_org_id,
        USER_LIST=user_list,
        okta_update_tag=okta_update_tag,
    )


def _sync_okta_users(neo4j_session, okta_org_id, okta_update_tag):
    """
    Sync okta users
    :param neo4j_session: Session with Neo4j server
    :param okta_org_id: Okta organization id to sync
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    logger.debug("Syncing Okta users")
    user_client = _create_user_client(okta_org_id)
    data = _get_okta_users(user_client)

    _load_okta_users(neo4j_session, okta_org_id, data, okta_update_tag)


def _get_okta_groups(api_client):
    """
    Get groups from Okta server
    :param api_client: Okta api client
    :return: Array of Dictionary containing group properties
    """
    group_list = []
    next_url = None

    # SDK Bug
    # get_paged_groups returns User object instead of UserGroup

    while True:
        try:
            # https://developer.okta.com/docs/reference/api/groups/#list-groups
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    'limit': 10000,
                }
                paged_response = api_client.get_path('/', params)
        except OktaError as okta_error:
            logger.debug(f"Got error while going through list group {okta_error}")
            break

        paged_results = PagedResults(paged_response, UserGroup)

        for current_group in paged_results.result:
            group_props = transform_okta_group(current_group)
            group_list.append(group_props)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return group_list


def transform_okta_group(okta_group):
    """
    Transform okta group object to consumable dictionary for graph
    :param okta_group: okta group object
    :return: Dictionary representing the group properties
    """
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/usergroup/UserGroup.py
    group_props = {}
    group_props["id"] = okta_group.id
    group_props["name"] = okta_group.profile.name
    group_props["description"] = okta_group.profile.description
    if okta_group.profile.samAccountName:
        group_props["sam_account_name"] = okta_group.profile.samAccountName
    else:
        group_props["sam_account_name"] = None

    if okta_group.profile.dn:
        group_props["dn"] = okta_group.profile.dn
    else:
        group_props["dn"] = None

    if okta_group.profile.windowsDomainQualifiedName:
        group_props["windows_domain_qualified_name"] = okta_group.profile.windowsDomainQualifiedName
    else:
        group_props["windows_domain_qualified_name"] = None

    if okta_group.profile.externalId:
        group_props["external_id"] = okta_group.profile.externalId
    else:
        group_props["external_id"] = None

    return group_props


def _sync_okta_groups(neo4_session, okta_org_id, okta_update_tag):
    """
    Synchronize okta groups
    :param neo4_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    logger.debug("Syncing Okta groups")
    api_client = _create_api_client(okta_org_id, "/api/v1/groups")

    data = _get_okta_groups(api_client)
    _load_okta_groups(neo4_session, okta_org_id, data, okta_update_tag)

    _load_okta_group_membership(neo4_session, api_client, okta_org_id, okta_update_tag)


def _create_okta_organization(neo4j_session, organization, okta_update_tag):
    """
    Create Okta organization in the graph
    :param neo4_session: session with the Neo4j server
    :param organization: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MERGE (org:OktaOrganization{id: {ORG_NAME}})
    ON CREATE SET org.name = org.id, org.firstseen = timestamp()
    SET org.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        ORG_NAME=organization,
        okta_update_tag=okta_update_tag,
    )


def _load_okta_groups(neo4j_session, okta_org_id, group_list, okta_update_tag):
    """
    Add okta groups to the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param group_list: group of list
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (org:OktaOrganization{id: {ORG_ID}})
    WITH org
    UNWIND {GROUP_LIST} as group_data
    MERGE (new_group:OktaGroup{id: group_data.id})
    ON CREATE SET new_group.firstseen = timestamp()
    SET new_group.name = group_data.name,
    new_group.description = group_data.description,
    new_group.sam_account_name = group_data.sam_account_name,
    new_group.dn = group_data.dn,
    new_group.windows_domain_qualified_name = group_data.windows_domain_qualified_name,
    new_group.external_id = group_data.external_id,
    new_group.lastupdated = {okta_update_tag}
    WITH new_group, org
    MERGE (org)-[org_r:RESOURCE]->(new_group)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        ORG_ID=okta_org_id,
        GROUP_LIST=group_list,
        okta_update_tag=okta_update_tag,
    )


def _get_okta_groups_id_from_graph(neo4j_session, okta_org_id):
    """
    Get the okta groups from the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :return: Array of group id
    """
    group_query = "MATCH (:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(group:OktaGroup) return group.id as id"

    result = neo4j_session.run(group_query, ORG_ID=okta_org_id)

    groups = [r['id'] for r in result]

    return groups


def _get_okta_application_id_from_graph(neo4j_session, okta_org_id):
    """
    Get the okta applications from the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :return: Array of application id
    """
    app_query = "MATCH (:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(app:OktaApplication) return app.id as id"

    result = neo4j_session.run(app_query, ORG_ID=okta_org_id)

    apps = [r['id'] for r in result]

    return apps


def _get_okta_group_members(api_client, group_id):
    """
    Get group members from Okta server
    :param api_client: Okta api client
    :param group_id: group to fetch members from
    :return: Array member id
    """
    member_list = []
    next_url = None

    while True:
        try:
            # https://developer.okta.com/docs/reference/api/groups/#list-group-members
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    'limit': 1000,
                }
                paged_response = api_client.get_path(f'{group_id}/users', params)
        except OktaError as okta_error:
            logger.debug(f"Got error while going through list group member {okta_error}")
            break

        member_results = transform_okta_group_member(paged_response.text)
        member_list.extend(member_results)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return member_list


def transform_okta_group_member(raw_json_response):
    """
    Transform group member object to graph consumable data
    :param raw_json_response: okta server response from list group members
    :return: array of member id
    """
    member_list = []
    member_results = json.loads(raw_json_response)

    for member in member_results:
        member_list.append(member["id"])

    return member_list


def _load_okta_group_membership(neo4j_session, api_client, okta_org_id, okta_update_tag):
    """
    Map group members in the graph
    :param neo4j_session: session with the Neo4j server
    :param api_client: Okta api client
    :param okta_org_id: Okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    for group_id in _get_okta_groups_id_from_graph(neo4j_session, okta_org_id):
        members = _get_okta_group_members(api_client, group_id)
        _ingest_okta_group_members(neo4j_session, group_id, members, okta_update_tag)


def _ingest_okta_group_members(neo4j_session, group_id, member_list, okta_update_tag):
    """
    Add group membership data into the graph
    :param neo4j_session: session with the Neo4j server
    :param group_id: group id to map
    :param member_list: group members
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MATCH (group:OktaGroup{id: {GROUP_ID}})
    WITH group
    UNWIND {MEMBER_LIST} as member_id
    MATCH (user:OktaUser{id: member_id})
    WITH group, user
    MERGE (user)-[r:MEMBER_OF_OKTA_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        GROUP_ID=group_id,
        MEMBER_LIST=member_list,
        okta_update_tag=okta_update_tag,
    )


def _get_okta_applications(app_client):
    """
    Get application data from Okta server
    :param app_client: api client
    :return: Array of dictionary containing application properties
    """
    app_list = []

    page_apps = app_client.get_paged_app_instances()

    while True:
        for current_application in page_apps.result:
            app_props = transform_okta_application(current_application)
            app_list.append(app_props)
        if not page_apps.is_last_page():
            # Keep on fetching pages of users until the last page
            page_apps = app_client.get_paged_app_instances(url=page_apps.next_url)
        else:
            break

    return app_list


def transform_okta_application(okta_application):
    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/app/AppInstance.py
    app_props = {}
    app_props["id"] = okta_application.id
    app_props["name"] = okta_application.name
    app_props["label"] = okta_application.label
    if okta_application.created:
        app_props["created"] = okta_application.created.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["created"] = None

    if okta_application.lastUpdated:
        app_props["okta_last_updated"] = okta_application.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["okta_last_updated"] = None

    app_props["status"] = okta_application.status

    if okta_application.activated:
        app_props["activated"] = okta_application.activated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        app_props["activated"] = None

    app_props["features"] = okta_application.features
    app_props["sign_on_mode"] = okta_application.signOnMode

    return app_props


def _load_okta_applications(neo4j_session, okta_org_id, app_list, okta_update_tag):
    """
    Add application into the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param app_list: application list - Array of dictionary
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (org:OktaOrganization{id: {ORG_ID}})
    WITH org
    UNWIND {APP_LIST} as app_data
    MERGE (new_app:OktaApplication{id: app_data.id})
    ON CREATE SET new_app.firstseen = timestamp()
    SET new_app.name = app_data.name,
    new_app.label = app_data.label,
    new_app.created = app_data.created,
    new_app.okta_last_updated = app_data.okta_last_updated,
    new_app.status = app_data.status,
    new_app.activated = app_data.activated,
    new_app.features = app_data.features,
    new_app.sign_on_mode = app_data.sign_on_mode,
    new_app.lastupdated = {okta_update_tag}
    WITH org, new_app
    MERGE (org)-[org_r:RESOURCE]->(new_app)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        ORG_ID=okta_org_id,
        APP_LIST=app_list,
        okta_update_tag=okta_update_tag,
    )


def _get_application_assigned_users(api_client, app_id):
    """
    Get users assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of user id
    """
    app_users = []

    next_url = None
    while True:
        try:
            # https://developer.okta.com/docs/reference/api/apps/#list-users-assigned-to-application
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    'limit': 500,
                }
                paged_response = api_client.get_path(f'/{app_id}/users', params)
        except OktaError as okta_error:
            logger.debug(f"Got error while going through list application assigned users {okta_error}")
            break

        for user_id in transform_application_users(paged_response.text):
            app_users.append(user_id)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_users


def transform_application_users(json_app_data):
    """
    Transform application users data for graph consumption
    :param json_app_data: raw json application data
    :return: individual user id as yield
    """

    app_data = json.loads(json_app_data)
    for user in app_data:
        yield user["id"]


def _is_last_page(response):
    """
    Determine if we are at the last page of a Paged result flow
    :param response: server response
    :return: boolean indicating if we are at the last page or not
    """
    # from https://github.com/okta/okta-sdk-python/blob/master/okta/framework/PagedResults.py
    return not ("next" in response.links)


def _get_application_assigned_groups(api_client, app_id):
    """
    Get groups assigned to a specific application
    :param api_client: api client
    :param app_id: application id to get users from
    :return: Array of group id
    """
    app_groups = []

    next_url = None

    while True:
        try:
            if next_url:
                paged_response = api_client.get(next_url)
            else:
                params = {
                    'limit': 500,
                }
                paged_response = api_client.get_path(f'/{app_id}/groups', params)
        except OktaError as okta_error:
            logger.debug(f"Got error while going through list application assigned groups {okta_error}")
            break

        for group_id in transform_applicationg_assigned_groups(paged_response.text):
            app_groups.append(group_id)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_groups


def transform_applicationg_assigned_groups(json_app_data):
    """
    Transform application group assignment to consumable data for the graph
    :param json_app_data: raw json group application assignment data.
    :return: group ids as yield
    """
    app_data = json.loads(json_app_data)

    for group in app_data:
        yield group["id"]


def _sync_okta_applications(neo4j_session, okta_org_id, okta_update_tag):
    """
    Sync okta application
    :param neo4j_session: session from the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    logger.debug("Syncing Okta Applications")

    app_client = _create_application_client(okta_org_id)

    data = _get_okta_applications(app_client)
    _load_okta_applications(neo4j_session, okta_org_id, data, okta_update_tag)

    api_client = _create_api_client(okta_org_id, "/api/v1/apps")

    for app in data:
        app_id = app["id"]
        user_list = _get_application_assigned_users(api_client, app_id)
        _ingest_application_user(neo4j_session, app_id, user_list, okta_update_tag)

        group_list = _get_application_assigned_groups(api_client, app_id)
        _ingest_application_group(neo4j_session, app_id, group_list, okta_update_tag)


def _ingest_application_user(neo4j_session, app_id, user_list, okta_update_tag):
    """
    Add application users into the graph
    :param neo4j_session: session with the Neo4j server
    :param app_id: application to map
    :param user_list: users to map
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MATCH (app:OktaApplication{id: {APP_ID}})
    WITH app
    UNWIND {USER_LIST} as user_id
    MATCH (user:OktaUser{id: user_id})
    WITH app, user
    MERGE (user)-[r:APPLICATION]->(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        APP_ID=app_id,
        USER_LIST=user_list,
        okta_update_tag=okta_update_tag,
    )


def _ingest_application_group(neo4j_session, app_id, group_list, okta_update_tag):
    """
    Add application groups into the graph
    :param neo4j_session: session with the Neo4j server
    :param app_id: application to map
    :param group_list: groups to map
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MATCH (app:OktaApplication{id: {APP_ID}})
    WITH app
    UNWIND {GROUP_LIST} as group_id
    MATCH (group:OktaGroup{id: group_id})
    WITH app, group
    MERGE (group)-[r:APPLICATION]->(app)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        APP_ID=app_id,
        GROUP_LIST=group_list,
        okta_update_tag=okta_update_tag,
    )


def _get_user_id_from_graph(neo4j_session, okta_org_id):
    """
    Get user id for the okta organization rom the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :return: Array od user id
    """
    group_query = "MATCH (:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(user:OktaUser) return user.id as id"

    result = neo4j_session.run(group_query, ORG_ID=okta_org_id)

    users = [r['id'] for r in result]

    return users


def _get_factor_for_user_id(factor_client, user_id):
    """
    Get factor for user from the Okta server
    :param factor_client: factor client
    :param user_id: user to fetch the data from
    :return: Array of dictionary containing factor properties
    """

    user_factors = []

    try:
        factor_results = factor_client.get_lifecycle_factors(user_id)
    except OktaError as okta_error:
        logger.debug(
            f"Unable to get factor for user id {user_id} with "
            f"error code {okta_error.error_code} with description {okta_error.error_summary}",
        )

        return []

    for current_factor in factor_results:
        factor_props = transform_okta_user_factor(current_factor)
        user_factors.append(factor_props)

    return user_factors


def transform_okta_user_factor(okta_factor_info):
    """
    Transform okta user factor into consumable data for the graph
    :param okta_factor_info: okta factor information
    :return: Dictionary of properties for the factor
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/factor/Factor.py
    factor_props = {}
    factor_props["id"] = okta_factor_info.id
    factor_props["factor_type"] = okta_factor_info.factorType
    factor_props["provider"] = okta_factor_info.provider
    factor_props["status"] = okta_factor_info.status
    if okta_factor_info.created:
        factor_props["created"] = okta_factor_info.created.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        factor_props["created"] = None

    if okta_factor_info.lastUpdated:
        factor_props["okta_last_updated"] = okta_factor_info.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        factor_props["okta_last_updated"] = None

    # we don't import Profile data into the graph due as it contains sensitive data
    return factor_props


def _ingest_user_factors(neo4j_session, user_id, factors, okta_update_tag):
    """
    Add user factors into the graph
    :param neo4j_session: session with the Neo4j server
    :param user_id: user to map factors to
    :param factors: factors to add
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest = """
    MATCH (user:OktaUser{id: {USER_ID}})
    WITH user
    UNWIND {FACTOR_LIST} as factor_data
    MERGE (new_factor:OktaUserFactor{id: factor_data.id})
    ON CREATE SET new_factor.firstseen = timestamp()
    SET new_factor.factor_type = factor_data.factor_type,
    new_factor.provider = factor_data.provider,
    new_factor.status = factor_data.status,
    new_factor.created = factor_data.created,
    new_factor.okta_last_updated = factor_data.okta_last_updated,
    new_factor.lastupdated = {okta_update_tag}
    WITH user, new_factor
    MERGE (user)-[r:FACTOR]->(new_factor)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        USER_ID=user_id,
        FACTOR_LIST=factors,
        okta_update_tag=okta_update_tag,
    )


def _sync_users_factors(neo4j_session, okta_org_id, okta_update_tag):
    """
    Sync user factors
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    logger.debug("Syncing Okta User Factors")

    factor_client = _create_factor_client(okta_org_id)
    users = _get_user_id_from_graph(neo4j_session, okta_org_id)

    for user_id in users:
        user_factors = _get_factor_for_user_id(factor_client, user_id)
        _ingest_user_factors(neo4j_session, user_id, user_factors, okta_update_tag)


def _get_user_roles(api_client, user_id, okta_org_id):
    """
    Get user roles from Okta
    :param api_client: api client
    :param user_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles
    response = api_client.get_path(f'/{user_id}/roles')

    return transform_user_roles_data(response.text, okta_org_id)


def transform_user_roles_data(data, okta_org_id):
    """
    Transform user role data
    :param data: data returned by Okta server
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """
    role_data = json.loads(data)

    user_roles = []

    for role in role_data:
        role_props = {}
        role_props["label"] = role["label"]
        role_props["type"] = role["type"]
        role_props["id"] = "{}-{}".format(okta_org_id, role["type"])

        user_roles.append(role_props)

    return user_roles


def _get_group_roles(api_client, group_id, okta_org_id):
    """
    Get user roles from Okta
    :param api_client: api client
    :param group_id: user to fetch roles from
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """

    # https://developer.okta.com/docs/reference/api/roles/#list-roles-assigned-to-group
    response = api_client.get_path(f'/{group_id}/roles')

    return transform_group_roles_data(response.text, okta_org_id)


def transform_group_roles_data(data, okta_org_id):
    """
    Transform user role data
    :param data: data returned by Okta server
    :param okta_org_id: okta organization id
    :return: Array of dictionary containing role properties
    """
    role_data = json.loads(data)

    user_roles = []

    for role in role_data:
        role_props = {}
        role_props["label"] = role["label"]
        role_props["type"] = role["type"]
        role_props["id"] = "{}-{}".format(okta_org_id, role["type"])

        user_roles.append(role_props)

    return user_roles


# TODO - Make this one fail gracefuly with warning as it requires super admin token
def _sync_roles(neo4j_session, okta_org_id, okta_update_tag):
    logger.debug("Syncing Okta Roles")

    # get API client
    api_client = _create_api_client(okta_org_id, "/api/v1/users")

    # users
    users = _get_user_id_from_graph(neo4j_session, okta_org_id)

    for user_id in users:
        user_roles = _get_user_roles(api_client, user_id, okta_org_id)
        if len(user_roles) > 0:
            _ingest_user_role(neo4j_session, user_id, user_roles, okta_update_tag)

    # groups
    groups = _get_okta_groups_id_from_graph(neo4j_session, okta_org_id)

    for group_id in groups:
        group_roles = _get_group_roles(api_client, group_id, okta_org_id)
        if len(group_roles) > 0:
            _ingest_group_role(neo4j_session, group_id, group_roles, okta_update_tag)


def _ingest_user_role(neo4j_session, user_id, roles_data, okta_update_tag):
    ingest = """
    MATCH (user:OktaUser{id: {USER_ID}})<-[:RESOURCE]-(org:OktaOrganization)
    WITH user,org
    UNWIND {ROLES_DATA} as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = {okta_update_tag}
    WITH user, role_node, org
    MERGE (user)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        USER_ID=user_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


def _ingest_group_role(neo4j_session, group_id, roles_data, okta_update_tag):
    ingest = """
    MATCH (group:OktaGroup{id: {GROUP_ID}})<-[:RESOURCE]-(org:OktaOrganization)
    WITH group,org
    UNWIND {ROLES_DATA} as role_data
    MERGE (role_node:OktaAdministrationRole{id: role_data.type})
    ON CREATE SET role_node.type = role_data.type, role_node.firstseen = timestamp()
    SET role_node.label = role_data.label, role_node.lastupdated = {okta_update_tag}
    WITH group, role_node, org
    MERGE (group)-[r:MEMBER_OF_OKTA_ROLE]->(role_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    WITH role_node, org
    MERGE (org)-[r2:RESOURCE]->(role_node)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        GROUP_ID=group_id,
        ROLES_DATA=roles_data,
        okta_update_tag=okta_update_tag,
    )


def _get_trusted_origins(api_client):
    """
    Get trusted origins from Okta
    :param api_client: api client
    :return: Array of dictionary containing trusted origins properties
    """

    response = api_client.get_path("/")
    return transform_trusted_origins(response.text)


def transform_trusted_origins(data):
    """
    Transform trusted origin data returned by Okta Server
    :param data: json response
    :return: Array of dictionary containing trusted origins properties
    """
    ret_list = []

    json_data = json.loads(data)
    for origin_data in json_data:
        props = {}
        props["id"] = origin_data["id"]
        props["name"] = origin_data["name"]
        props["origin"] = origin_data["origin"]

        # https://developer.okta.com/docs/reference/api/trusted-origins/#scope-object
        scope_types = []
        for scope in origin_data.get("scopes", []):
            scope_types.append(scope["type"])

        props["scopes"] = scope_types
        props["status"] = origin_data["status"]
        props["created"] = origin_data.get("created", None)
        props["created_by"] = origin_data.get("createdBy", None)
        props["okta_last_updated"] = origin_data.get("lastUpdated", None)
        props["okta_last_updated_by"] = origin_data.get("lastUpdatedBy", None)

        ret_list.append(props)

    return ret_list


def _ingest_trusted_origins(neo4j_session, okta_org_id, trusted_list, okta_update_tag):
    """
    Add trusted origins to the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param trusted_list: list of trusted origins
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest = """
    MATCH (org:OktaOrganization{id: {ORG_ID}})
    WITH org
    UNWIND {TRUSTED_LIST} as data
    MERGE (new:OktaTrustedOrigin{id: data.id})
    ON CREATE SET new.firstseen = timestamp()
    SET new.name = data.name,
    new.origin = data.origin,
    new.scopes = data.scoped,
    new.status = data.status,
    new.created = data.created,
    new.created_by = data.created_by,
    new.okta_last_updated = data.okta_last_updated,
    new.okta_last_updated_by = data.okta_last_updated_by,
    new.lastupdated = {okta_update_tag}
    WITH org, new
    MERGE (org)-[r:RESOURCE]->(new)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        ORG_ID=okta_org_id,
        TRUSTED_LIST=trusted_list,
        okta_update_tag=okta_update_tag,
    )


def _sync_trusted_origins(neo4j_session, okta_org_id, okta_update_tag):
    """
    Sync trusted origins
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    logger.debug("Syncing Okta Trusted Origins")

    api_client = _create_api_client(okta_org_id, "/api/v1/trustedOrigins")

    trusted_list = _get_trusted_origins(api_client)
    _ingest_trusted_origins(neo4j_session, okta_org_id, trusted_list, okta_update_tag)


def sync(neo4j_session, config):
    """
    Starts the Okta ingestion process by initializing Okta API session and pulling necessary information
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """

    okta_organization = config.okta_organization

    logger.debug(f"Starting Okta sync on {okta_organization}")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "OKTA_ORG_ID": okta_organization,
    }

    _create_okta_organization(neo4j_session, okta_organization, config.update_tag)
    _sync_okta_users(neo4j_session, okta_organization, config.update_tag)
    _sync_okta_groups(neo4j_session, okta_organization, config.update_tag)
    _sync_okta_applications(session, okta_organization, last_update)
    _sync_users_factors(session, okta_organization, last_update)
    _sync_trusted_origins(session, okta_organization, last_update)

    # need creds with permission
    # soft fail as some won't be able to get such high priv token
    try:
        _sync_roles(session, okta_organization, last_update)
    except Exception as exception:
        print("Unable to sync admin roles - api token needs admin rights to pull admin roles data")
        logger.warning(f"Unable to pull admin roles got {exception}")

    _cleanup_okta_organizations(neo4j_session, common_job_parameters)


def _cleanup_okta_organizations(session, common_job_parameters):
    """
    Remove stale Okta organization
    :param session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :param okta_organization: Okta org id to cleanup
    :return: Nothing
    """

    run_cleanup_job('okta_import_cleanup.json', session, common_job_parameters)


if __name__ == '__main__':
    import time
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver("bolt://localhost:7687")

    with driver.session() as session:
        last_update = int(time.time())

        config = Config(
            neo4j_uri="7687",
            neo4j_user="neo4j",
            neo4j_password="1",
            update_tag=last_update,
            okta_organization="lyft",
        )

        sync(session, config)

# Okta intel module - Applications
import json
import logging

from okta import AppInstanceClient
from okta.framework.OktaError import OktaError

from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page

logger = logging.getLogger(__name__)


def _create_application_client(okta_org, okta_api_key):
    """
    Create Okta AppInstanceClient
    :param okta_org: Okta organization name
    :param okta_api_key: Okta API key
    :return: Instance of AppInstanceClient
    """
    app_client = AppInstanceClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=okta_api_key,
    )

    return app_client


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

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_users


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

        for group_id in transform_application_assigned_groups(paged_response.text):
            app_groups.append(group_id)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_groups


def transform_application_users(json_app_data):
    """
    Transform application users data for graph consumption
    :param json_app_data: raw json application data
    :return: individual user id
    """

    users = []
    app_data = json.loads(json_app_data)
    for user in app_data:
        users.append(user["id"])

    return users


def transform_application_assigned_groups(json_app_data):
    """
    Transform application group assignment to consumable data for the graph
    :param json_app_data: raw json group application assignment data.
    :return: group ids
    """
    groups = []
    app_data = json.loads(json_app_data)

    for group in app_data:
        groups.append(group["id"])

    return groups


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


def _load_application_user(neo4j_session, app_id, user_list, okta_update_tag):
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


def _load_application_group(neo4j_session, app_id, group_list, okta_update_tag):
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


def sync_okta_applications(neo4j_session, okta_org_id, okta_update_tag, okta_api_key):
    """
    Sync okta application
    :param neo4j_session: session from the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta api key
    :return: Nothing
    """
    logger.debug("Syncing Okta Applications")

    app_client = _create_application_client(okta_org_id, okta_api_key)

    data = _get_okta_applications(app_client)
    _load_okta_applications(neo4j_session, okta_org_id, data, okta_update_tag)

    api_client = create_api_client(okta_org_id, "/api/v1/apps")

    for app in data:
        app_id = app["id"]
        user_list = _get_application_assigned_users(api_client, app_id)
        _load_application_user(neo4j_session, app_id, user_list, okta_update_tag)

        group_list = _get_application_assigned_groups(api_client, app_id)
        _load_application_group(neo4j_session, app_id, group_list, okta_update_tag)

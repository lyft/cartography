# Okta intel module
import logging
import json
from okta import UsersClient, UserGroupsClient, AppInstanceClient, FactorsClient
from okta.framework.PagedResults import PagedResults
from okta.models.usergroup import UserGroup
from okta.framework.ApiClient import ApiClient
from okta.framework.OktaError import OktaError
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


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

            # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/UserProfile.py
            user_props = {}
            user_props["first_name"] = current_user.profile.firstName
            user_props["last_name"] = current_user.profile.lastName
            user_props["login"] = current_user.profile.login
            user_props["email"] = current_user.profile.email
            user_props["second_email"] = current_user.profile.secondEmail
            user_props["mobile_phone"] = current_user.profile.mobilePhone

            # https://github.com/okta/okta-sdk-python/blob/master/okta/models/user/User.py
            user_props["id"] = current_user.id
            user_props["created"] = current_user.created.strftime("%m/%d/%Y, %H:%M:%S")
            if current_user.activated:
                user_props["activated"] = current_user.activated.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                user_props["activated"] = None

            if current_user.statusChanged:
                user_props["status_changed"] = current_user.statusChanged.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                user_props["status_changed"] = None

            if current_user.lastLogin:
                user_props["last_login"] = current_user.lastLogin.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                user_props["last_login"] = None

            if current_user.lastUpdated:
                user_props["okta_last_updated"] = current_user.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                user_props["okta_last_updated"] = None

            if current_user.passwordChanged:
                user_props["password_changed"] = current_user.passwordChanged.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                user_props["password_changed"] = None

            if current_user.transitioningToStatus:
                user_props["transition_to_status"] = current_user.transitioningToStatus
            else:
                user_props["transition_to_status"] = None

            # TODO : Handle links

            user_list.append(user_props)
        if not paged_users.is_last_page():
            # Keep on fetching pages of users until the last page
            paged_users = user_client.get_paged_users(url=paged_users.next_url)
        else:
            break

    return user_list


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

    neo4j_session.run(ingest_statement,
                      ORG_ID=okta_org_id,
                      USER_LIST=user_list,
                      okta_update_tag=okta_update_tag)


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


def _create_user_client(okta_org):
    """
    Create Okta User Client
    :param okta_org: Okta organization name
    :return: Instance of UsersClient
    """
    # http://developer.okta.com/docs/api/getting_started/getting_a_token.html
    user_client = UsersClient(base_url="https://{0}.okta.com/".format(okta_org),
                              api_token='')

    return user_client


def _create_group_client(okta_org):
    """
    Create Okta UserGroupsClient
    :param okta_org: Okta organization name
    :return: Instance of UserGroupsClient
    """
    usergroups_client = UserGroupsClient(base_url="https://{0}.okta.com/".format(okta_org),
                                         api_token='')

    return usergroups_client


def _create_application_client(okta_org):
    """
    Create Okta AppInstanceClient
    :param okta_org: Okta organization name
    :return: Instance of AppInstanceClient
    """
    app_client = AppInstanceClient(base_url="https://{0}.okta.com/".format(okta_org),
                                   api_token='')

    return app_client


def _create_factor_client(okta_org):
    """
    Create Okta FactorsClient
    :param okta_org: Okta organization name
    :return: Instance of FactorsClient
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/FactorsClient.py
    factor_client = FactorsClient(base_url="https://{0}.okta.com/".format(okta_org),
                                  api_token='')

    return factor_client


def _create_api_client(okta_org, path_name):
    """
    Create Okta ApiClient
    :param okta_org: Okta organization name
    :param path_name: API Path
    :return: Instance of ApiClient
    """
    api_client = ApiClient(base_url="https://{0}.okta.com/".format(okta_org),
                           pathname=path_name,
                           api_token='')

    return api_client


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
                    'limit': 10000
                }
                paged_response = api_client.get_path('/', params)
        except OktaError as okta_error:
            break

        paged_results = PagedResults(paged_response, UserGroup)

        for current_group in paged_results.result:

            # https://github.com/okta/okta-sdk-python/blob/master/okta/models/usergroup/UserGroup.py
            group_props = {}
            group_props["id"] = current_group.id
            group_props["name"] = current_group.profile.name
            group_props["description"] = current_group.profile.description
            if current_group.profile.samAccountName:
                group_props["sam_account_name"] = current_group.profile.samAccountName
            else:
                group_props["sam_account_name"] = None

            if current_group.profile.dn:
                group_props["dn"] = current_group.profile.dn
            else:
                group_props["dn"] = None

            if current_group.profile.windowsDomainQualifiedName:
                group_props["windows_domain_qualified_name"] = current_group.profile.windowsDomainQualifiedName
            else:
                group_props["windows_domain_qualified_name"] = None

            if current_group.profile.externalId:
                group_props["external_id"] = current_group.profile.externalId
            else:
                group_props["external_id"] = None

            # TODO : Handle links

            group_list.append(group_props)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return group_list


def _sync_okta_groups(neo4_session, okta_org_id, okta_update_tag):
    """
    Synchronize okta groups
    :param neo4_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    logger.debug("Syncing Okta groups")
    api_client = _create_api_client(okta_org_id, "/api/v1/groups" )

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

    neo4j_session.run(ingest,
                      ORG_NAME=organization,
                      okta_update_tag=okta_update_tag)


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

    neo4j_session.run(ingest_statement,
                      ORG_ID=okta_org_id,
                      GROUP_LIST=group_list,
                      okta_update_tag=okta_update_tag)


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

    result = neo4j_session.run(group_query, ORG_ID=okta_org_id)

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
                    'limit': 1000
                }
                paged_response = api_client.get_path('{0}/users'.format(group_id), params)
        except OktaError as okta_error:
            break

        member_results = json.loads(paged_response.text)

        for member in member_results:
            member_list.append(member.id)

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

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

    neo4j_session.run(ingest,
                      GROUP_ID=group_id,
                      MEMBER_LIST=member_list,
                      okta_update_tag=okta_update_tag)


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

            # https://github.com/okta/okta-sdk-python/blob/master/okta/models/app/AppInstance.py
            app_props = {}
            app_props["id"] = current_application.id
            app_props["name"] = current_application.name
            app_props["label"] = current_application.label
            if current_application.created:
                app_props["created"] = current_application.created.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                app_props["created"] = None

            if current_application.lastUpdated:
                app_props["okta_last_updated"] = current_application.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                app_props["okta_last_updated"] = None

            app_props["status"] = current_application.status

            if current_application.activated:
                app_props["activated"] = current_application.activated.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                app_props["activated"] = None

            app_props["features"] = current_application.features
            app_props["sign_on_mode"] = current_application.signOnMode


            # TODO handle Accessibility, Visibility, Settings

            app_list.append(app_props)
        if not page_apps.is_last_page():
            # Keep on fetching pages of users until the last page
            page_apps = app_client.get_paged_app_instances(url=page_apps.next_url)
        else:
            break

    return app_list


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

    neo4j_session.run(ingest_statement,
                      ORG_ID=okta_org_id,
                      APP_LIST=app_list,
                      okta_update_tag=okta_update_tag)


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
                    'limit': 500
                }
                paged_response = api_client.get_path('/{0}/users'.format(app_id), params)
        except OktaError as okta_error:
            break

        app_data = json.loads(paged_response.text)
        for user in app_data:
            app_users.append(user["id"])

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_users


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
                    'limit': 500
                }
                paged_response = api_client.get_path('/{0}/groups'.format(app_id), params)
        except OktaError as okta_error:
            break

        app_data = json.loads(paged_response.text)

        for group in app_data:
            app_groups.append(group["id"])

        if not _is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return app_groups


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

    neo4j_session.run(ingest,
                      APP_ID=app_id,
                      USER_LIST=user_list,
                      okta_update_tag=okta_update_tag)


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

    neo4j_session.run(ingest,
                      APP_ID=app_id,
                      GROUP_LIST=group_list,
                      okta_update_tag=okta_update_tag)


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
        logger.debug("Unable to get factor for user id {0} with" \
                     "error code {1} with description {2}".format(user_id,
                                                                  okta_error.error_code,
                                                                  okta_error.error_summary))
        return []

    for current_factor in factor_results:

        # https://github.com/okta/okta-sdk-python/blob/master/okta/models/factor/Factor.py
        factor_props = {}
        factor_props["id"] = current_factor.id
        factor_props["factor_type"] = current_factor.factorType
        factor_props["provider"] = current_factor.provider
        factor_props["status"] = current_factor.status
        if current_factor.created:
            factor_props["created"] = current_factor.created.strftime("%m/%d/%Y, %H:%M:%S")
        else:
            current_factor["created"] = None

        if current_factor.lastUpdated:
            factor_props["okta_last_updated"] = current_factor.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
        else:
            current_factor["okta_last_updated"] = None

        # we don't import Profile data into the graph due as it contains sensitive data

        user_factors.append(factor_props)

    return user_factors


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

    neo4j_session.run(ingest,
                      USER_ID=user_id,
                      FACTOR_LIST=factors,
                      okta_update_tag=okta_update_tag)


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


def _get_user_roles(api_client, user_id):
    """
    Get user roles from Okta
    :param api_client: api client
    :param user_id: user to fetch roles from
    :return: Array of dictionary containing role properties
    """

    user_roles = []

    # https://developer.okta.com/docs/reference/api/roles/#role-assignment-operations
    response = api_client.get_path('/{0}/roles'.format(user_id))

    role_data = json.loads(response.text)

    for role in role_data:
        role_props = {}
        role_props["id"] = role["id"]
        role_props["label"] = role["label"]
        role_props["type"] = role["type"]

        user_roles.append(role_props)

    return user_roles


# TODO - Get token with role permission
# def _sync_roles(neo4j_session, okta_org_id, okta_update_tag):
#     logger.debug("Syncing Okta Roles")
#
#     # get API client
#     api_client = _create_api_client(okta_org_id, "/api/v1/users")
#
#     # users
#     users = _get_user_id_from_graph(neo4j_session, okta_org_id)
#
#     for user_id in users:
#         user_roles = _get_user_roles(api_client, user_id)
#         print(user_roles)
#     #     # _ingest_user_factors(neo4j_session, user_id, user_factors, okta_update_tag)

def _get_trusted_origins(api_client):
    """
    Get trusted origins from Okta
    :param api_client: api client
    :return: Array of dictionary containing trusted origins properties
    """

    ret_list = []

    response = api_client.get_path("/")
    response_list = json.loads(response.text)

    for data in response_list:
        props = {}
        props["id"] = data["id"]
        props["name"] = data["name"]

        # https://developer.okta.com/docs/reference/api/trusted-origins/#scope-object
        scope_types = []
        for scope in data.get("scopes", []):
            scope_types.append(scope["type"])

        props["scopes"] = scope_types
        props["status"] = data["status"]
        props["created"] = data.get("created", None)
        props["created_by"] = data.get("created_by", None)
        props["okta_last_updated"] = data.get("lastUpdated", '')
        props["okta_last_updated_by"] = data["lastUpdatedBy"]

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

    neo4j_session.run(ingest,
                      ORG_ID=okta_org_id,
                      TRUSTED_LIST=trusted_list,
                      okta_update_tag=okta_update_tag)


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


def start_okta_ingestion(neo4j_session, okta_organization, config):
    """
    Starts the Okta ingestion process by initializing Okta API session and pulling necessary information
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "OKTA_ORG_ID": okta_organization,
    }

    _create_okta_organization(neo4j_session, okta_organization, config.update_tag)
    _sync_okta_users(neo4j_session, config.update_tag)
    _sync_okta_groups(neo4j_session, config.update_tag)
    _sync_okta_applications(session, org_id, last_update)
    _sync_users_factors(session, org_id, last_update)
    _sync_trusted_origins(session, org_id, last_update)

    # need creds with permission
    # _sync_roles(session, org_id, last_update)

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

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1"))

    with driver.session() as session:
        last_update = int(time.time())
        org_id = "lyft"

        # start_okta_ingestion(session, "lyft", {})
        _create_okta_organization(session, org_id, last_update)
        _sync_okta_users(session, org_id, last_update)
        _sync_okta_groups(session, org_id, last_update)
        _sync_okta_applications(session, org_id, last_update)
        _sync_users_factors(session, org_id, last_update)
        _sync_trusted_origins(session, org_id, last_update)

        # need creds with permission
        # _sync_roles(session, org_id, last_update)

        common_job_parameters = {
            "UPDATE_TAG": last_update,
            "OKTA_ORG_ID": org_id,
        }
        _cleanup_okta_organizations(session, common_job_parameters)

    # # http://developer.okta.com/docs/api/getting_started/getting_a_token.html
    # usersClient = UsersClient(base_url='https://lyft.okta.com/',
    #                           api_token='00ig0il4HVi4GBlm9_chkwruYCaVuysKgomChun72Y')
    #
    # users = usersClient.get_paged_users()
    #
    # while True:
    #     for user in users.result:
    #         print(u"First Name: {}".format(user.profile.firstName))
    #         print(u"Last Name:  {}".format(user.profile.lastName))
    #         print(u"Login:      {}".format(user.profile.login))
    #         print(u"User ID:    {}\n".format(user.id))
    #     if not users.is_last_page():
    #         # Keep on fetching pages of users until the last page
    #         users = usersClient.get_paged_users(url=users.next_url)
    #     else:
    #         break

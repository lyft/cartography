# Okta intel module
import logging
from okta import UsersClient, UserGroupsClient, AppInstanceClient
# from okta import UserGroupsClient
# from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def _get_okta_users(user_client):
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
            user_props["created"] = current_user.created.today().timestamp()
            if current_user.activated:
                user_props["activated"] = current_user.activated.today().timestamp()
            else:
                user_props["activated"] = None

            if current_user.statusChanged:
                user_props["status_changed"] = current_user.statusChanged.today().timestamp()
            else:
                user_props["status_changed"] = None

            if current_user.lastLogin:
                user_props["last_login"] = current_user.lastLogin.today().timestamp()
            else:
                user_props["last_login"] = None

            if current_user.lastUpdated:
                user_props["okta_last_updated"] = current_user.lastUpdated.today().timestamp()
            else:
                user_props["okta_last_updated"] = None

            if current_user.passwordChanged:
                user_props["password_changed"] = current_user.passwordChanged.today().timestamp()
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
    # """
    # Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    # :param session: The Neo4j session
    # :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    # See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    # :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    # :param common_job_parameters: Parameters to carry to the Neo4j jobs
    # :return: Nothing
    # """

    logger.debug("Syncing Okta users")
    user_client = _create_user_client(okta_org_id)
    data = _get_okta_users(user_client)

    _load_okta_users(neo4j_session, okta_org_id, data, okta_update_tag)


# def _cleanup_okta_data(neo4j_session, common_job_parameters):
#     """
#     Remove stale Okta nodes and relationships
#     :param neo4j_session: The Neo4j session
#     :param common_job_parameters: Parameters to carry to the cleanup job
#     :return: Nothing
#     """
#     run_cleanup_job('okta_import_cleanup.json', neo4j_session, common_job_parameters)


def _create_user_client(okta_org):
    # http://developer.okta.com/docs/api/getting_started/getting_a_token.html
    usersClient = UsersClient(base_url="https://{0}.okta.com/".format(okta_org),
                              api_token='')

    return usersClient


def _create_group_client(okta_org):
    # http://developer.okta.com/docs/api/getting_started/getting_a_token.html
    usergroups_client = UserGroupsClient(base_url="https://{0}.okta.com/".format(okta_org),
                                         api_token='')

    return usergroups_client


def _create_application_client(okta_org):

    appClient = AppInstanceClient(base_url="https://{0}.okta.com/".format(okta_org),
                                  api_token='')

    return appClient


def _get_okta_groups(group_client):
    group_list = []

    # SDK Bug
    # get_paged_groups returns User object instead of UserGroup
    # paged_groups = group_client.get_paged_groups()
    # Ticket filed - https://github.com/okta/okta-sdk-python/issues/75
    group_results = group_client.get_groups()

    for current_group in group_results:

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

    return group_list


# Get Paged Groups returns User object - Buggy SDK
# def _get_okta_groups(group_client):
#     group_list = []
#     paged_groups = group_client.get_paged_groups()
#
#     while True:
#         for current_group in paged_groups.result:
#             # https://github.com/okta/okta-sdk-python/blob/master/okta/models/usergroup/UserGroup.py
#             group_props = {}
#             group_props["id"] = current_group.id
#             group_props["name"] = current_group.profile.name
#             group_props["description"] = current_group.profile.description
#             if current_group.profile.samAccountName:
#                 group_props["sam_account_name"] = current_group.profile.samAccountName
#             else:
#                 group_props["sam_account_name"] = None
#
#             if current_group.profile.dn:
#                 group_props["dn"] = current_group.profile.dn
#             else:
#                 group_props["dn"] = None
#
#             if current_group.profile.windowsDomainQualifiedName:
#                 group_props["windows_domain_qualified_name"] = current_group.profile.windowsDomainQualifiedName
#             else:
#                 group_props["windows_domain_qualified_name"] = None
#
#             if current_group.profile.externalId:
#                 group_props["external_id"] = current_group.profile.externalId
#             else:
#                 group_props["external_id"] = None
#
#             # TODO : Handle links
#
#             group_list.append(group_props)
#
#         if not paged_groups.is_last_page():
#             # Keep on fetching pages of groups until the last page
#             paged_groups = group_client.get_paged_groups(url=paged_groups.next_url)
#         else:
#             break
#
#     return group_list


def _sync_okta_groups(neo4_session, okta_org_id, okta_update_tag):
    logger.debug("Syncing Okta groups")
    group_client = _create_group_client(okta_org_id)

    data = _get_okta_groups(group_client)
    _load_okta_groups(neo4_session, okta_org_id, data, okta_update_tag)

    _load_okta_group_membership(neo4_session, group_client, okta_update_tag)


def start_okta_ingestion(neo4j_session, okta_organization, config) -> None:
    """
    Starts the Okta ingestion process by initializing Okta API session and pulling necessary information
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    _create_okta_organization(neo4j_session, okta_organization, config.update_tag)
    _sync_okta_users(neo4j_session, config.update_tag)
    _sync_okta_groups(neo4j_session, config.update_tag)

    # _cleanup_okta_data(neo4j_session, common_job_parameters)


def _create_okta_organization(neo4j_session, organization, okta_update_tag):
    ingest = """
    MERGE (org:OktaOrganization{id: {ORG_NAME}})
    ON CREATE SET org.name = org.id, org.firstseen = timestamp()
    SET org.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(ingest,
                      ORG_NAME=organization,
                      okta_update_tag=okta_update_tag)


def _load_okta_groups(neo4j_session, okta_org_id, group_list, okta_update_tag):
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
    MERGE (org)-[org_r:RESOURCE]->(new_user)
    ON CREATE SET org_r.firstseen = timestamp()
    SET org_r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(ingest_statement,
                      ORG_ID=okta_org_id,
                      GROUP_LIST=group_list,
                      okta_update_tag=okta_update_tag)


def _get_okta_groups_id_from_graph(neo4j_session):
    group_query = "MATCH (group:OktaGroup) return group.id as id"

    result = neo4j_session.run(group_query)

    groups = [r['id'] for r in result]

    return groups


def _get_okta_application_id_from_graph(neo4j_session):
    app_query = "MATCH (app:OktaApplication) return app.id as id"

    result = neo4j_session.run(group_query)

    apps = [r['id'] for r in result]

    return apps


def _get_okta_group_members(group_client, group_id):
    member_list = []

    member_results = group_client.get_group_users(group_id)

    for member in member_results:
        member_list.append(member.id)

    return member_list


def _load_okta_group_membership(neo4j_session, group_client, okta_update_tag):

    for group_id in _get_okta_groups_id_from_graph(neo4j_session):
        members = _get_okta_group_members(group_client, group_id)
        _ingest_okta_group_members(neo4j_session, group_id, members, okta_update_tag)


def _ingest_okta_group_members(neo4j_session, group_id, member_list, okta_update_tag):
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
                app_props["created"] = current_application.created.today().timestamp()
            else:
                app_props["created"] = None

            if current_application.lastUpdated:
                app_props["okta_last_updated"] = current_application.lastUpdated.today().timestamp()
            else:
                app_props["okta_last_updated"] = None

            app_props["status"] = current_application.status

            if current_application.activated:
                app_props["activated"] = current_application.activated.today().timestamp()
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


def _sync_okta_applications(neo4_session, okta_org_id, okta_update_tag):
    logger.debug("Syncing Okta Applications")

    app_client = _create_application_client(okta_org_id)

    data = _get_okta_applications(app_client)
    _load_okta_applications(neo4_session, okta_org_id, data, okta_update_tag)


# def _load_okta_application_membership(neo4j_session, app_client, okta_update_tag):
#
#     for app_id in _get_okta_application_id_from_graph(neo4j_session):
#         user_assignment = _get_okta_application_user_assignment(app_client, app_id)
#         _ingest_okta_application_user_assignment(neo4j_session, app_id, user_assignment, okta_update_tag)
#
#         group_assignment = _get_okta_application_group_assignment(app_client, app_id)
#         _ingest_okta_application_group_assignment(neo4j_session, app_id, group_assignment, okta_update_tag)

# def _get_okta_application_user_assignment(app_client, app_id):
#     member_list = []
#
#     member_results = app_client.get_group_users(group_id)
#
#     for member in member_results:
#         member_list.append(member.id)
#
#     return member_list


if __name__ == '__main__':
    import time
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1"))

    with driver.session() as session:
        last_update = int(time.time())
        _create_okta_organization(session, "lyft", last_update)
        _sync_okta_users(session, "lyft", last_update)
        _sync_okta_groups(session, "lyft", last_update)
        _sync_okta_applications(session, "lyft", last_update)

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

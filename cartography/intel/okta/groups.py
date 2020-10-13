# Okta intel module - Group
import json
import logging

from okta.framework.OktaError import OktaError
from okta.framework.PagedResults import PagedResults
from okta.models.usergroup import UserGroup

from cartography.intel.okta.utils import create_api_client
from cartography.intel.okta.utils import is_last_page
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_okta_groups(api_client):
    """
    Get groups from Okta server
    :param api_client: Okta api client
    :return: Array of group information
    """
    group_list = []
    next_url = None

    # SDK Bug
    # get_paged_groups returns User object instead of UserGroup

    while True:
        # https://developer.okta.com/docs/reference/api/groups/#list-groups
        if next_url:
            paged_response = api_client.get(next_url)
        else:
            params = {
                'limit': 10000,
            }
            paged_response = api_client.get_path('/', params)

        paged_results = PagedResults(paged_response, UserGroup)

        group_list.extend(paged_results.result)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return group_list


@timeit
def _get_okta_group_members(api_client, group_id):
    """
    Get group members from Okta server
    :param api_client: Okta api client
    :param group_id: group to fetch members from
    :return: Array or group membership information
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
                paged_response = api_client.get_path(f'/{group_id}/users', params)
        except OktaError as okta_error:
            logger.debug(f"Got error while going through list group member {okta_error}")
            break

        member_list.append(paged_response.text)

        if not is_last_page(paged_response):
            next_url = paged_response.links.get("next").get("url")
        else:
            break

    return member_list


@timeit
def transform_okta_group_list(okta_group_list):
    groups = []
    groups_id = []

    for current in okta_group_list:
        groups.append(transform_okta_group(current))
        groups_id.append(current.id)

    return groups, groups_id


@timeit
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


@timeit
def transform_okta_group_member_list(okta_member_list):
    member_list = []

    for current in okta_member_list:
        member_list.extend(transform_okta_group_member(current))

    return member_list


@timeit
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


@timeit
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


@timeit
def _load_okta_group_members(neo4j_session, group_id, member_list, okta_update_tag):
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


@timeit
def _sync_okta_group_membership(neo4j_session, api_client, group_list_info, okta_update_tag):
    """
    Map group members in the graph
    :param neo4j_session: session with the Neo4j server
    :param api_client: Okta api client
    :param group_list_info: Group information as list
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    for group_info in group_list_info:
        group_id = group_info["id"]
        members_data = _get_okta_group_members(api_client, group_id)
        members = transform_okta_group_member_list(members_data)
        _load_okta_group_members(neo4j_session, group_id, members, okta_update_tag)


@timeit
def sync_okta_groups(neo4_session, okta_org_id, okta_update_tag, okta_api_key, sync_state):
    """
    Synchronize okta groups
    :param neo4_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :param sync_state: Okta sync state
    :return: Nothing
    """
    logger.debug("Syncing Okta groups")
    api_client = create_api_client(okta_org_id, "/api/v1/groups", okta_api_key)

    okta_group_data = _get_okta_groups(api_client)
    group_list_info, group_ids = transform_okta_group_list(okta_group_data)

    # store result for later use
    sync_state.groups = group_ids

    _load_okta_groups(neo4_session, okta_org_id, group_list_info, okta_update_tag)

    _sync_okta_group_membership(neo4_session, api_client, group_list_info, okta_update_tag)

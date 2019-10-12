# Okta intel module - utility functions
from okta.framework.ApiClient import ApiClient


def is_last_page(response):
    """
    Determine if we are at the last page of a Paged result flow
    :param response: server response
    :return: boolean indicating if we are at the last page or not
    """
    # from https://github.com/okta/okta-sdk-python/blob/master/okta/framework/PagedResults.py
    return not ("next" in response.links)


def get_user_id_from_graph(neo4j_session, okta_org_id):
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


def get_okta_groups_id_from_graph(neo4j_session, okta_org_id):
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


def create_api_client(okta_org, path_name, api_key):
    """
    Create Okta ApiClient
    :param okta_org: Okta organization name
    :param path_name: API Path
    :param api_key: Okta api key
    :return: Instance of ApiClient
    """
    api_client = ApiClient(
        base_url=f"https://{okta_org}.okta.com/",
        pathname=path_name,
        api_token=api_key,
    )

    return api_client

import logging

from cartography.intel.github.util import fetch_all
from cartography.util import timeit

logger = logging.getLogger(__name__)


GITHUB_ORG_USERS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            membersWithRole(first:100, after: $cursor){
                edges {
                    hasTwoFactorEnabled
                    node {
                        login
                        name
                        isSiteAdmin
                        resourcePath
                    }
                    role
                }
                pageInfo{
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """


@timeit
def get(token, api_url, organization):
    """
    Retrieve a list of users from a Github organization as described in
    https://docs.github.com/en/graphql/reference/objects#organizationmemberedge.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A list of dicts representing users. Has shape
    [ {'cursor': '...', 'hasTwoFactorEnabled': None, 'node': {'isSiteAdmin': False, 'login': 'name'}, 'role': 'MEMBER'}
      , ... ]
    """
    return fetch_all(token, api_url, organization, GITHUB_ORG_USERS_PAGINATED_GRAPHQL, 'membersWithRole', 'edges')


@timeit
def load(neo4j_session, user_data, update_tag):
    query = """
    UNWIND {UserData} as user
    MERGE (u:GitHubUser{id: user.node.resourcePath})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = user.node.name,
    u.login = user.node.login,
    u.has_2fa_enabled = user.hasTwoFactorEnabled,
    u.role = user.role,
    u.is_site_admin = user.node.isSiteAdmin,
    u.lastupdated = {UpdateTag}"""

    neo4j_session.run(
        query,
        UserData=user_data,
        UpdateTag=update_tag,
    )

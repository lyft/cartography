import logging

from cartography.util import timeit
from cartography.intel.github.util import fetch_all

logger = logging.getLogger(__name__)


GITHUB_ORG_USERS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            membersWithRole(first:100, after: $cursor){
                edges {
                    cursor
                    hasTwoFactorEnabled
                    node {
                        login
                        name
                        isSiteAdmin
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


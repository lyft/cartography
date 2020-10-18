import logging

from cartography.intel.github.util import fetch_all
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


GITHUB_ORG_USERS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            url
            login
            membersWithRole(first:100, after: $cursor){
                edges {
                    hasTwoFactorEnabled
                    node {
                        url
                        login
                        name
                        isSiteAdmin
                        email
                        company
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
    Retrieve a list of users from the given GitHub organization as described in
    https://docs.github.com/en/graphql/reference/objects#organizationmemberedge.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A 2-tuple containing 1. a list of dicts representing users - see tests.data.github.users.GITHUB_USER_DATA
    for shape, and 2. data on the owning GitHub organization - see tests.data.github.users.GITHUB_ORG_DATA for shape.
    """
    users, org = fetch_all(token, api_url, organization, GITHUB_ORG_USERS_PAGINATED_GRAPHQL, 'membersWithRole', 'edges')
    return users, org


@timeit
def load_organization_users(neo4j_session, user_data, org_data, update_tag):
    query = """
    MERGE (org:GitHubOrganization{id: {OrgUrl}})
    ON CREATE SET org.firstseen = timestamp()
    SET org.username = {OrgLogin},
    org.lastupdated = {UpdateTag}
    WITH org

    UNWIND {UserData} as user

    MERGE (u:GitHubUser{id: user.node.url})
    ON CREATE SET u.firstseen = timestamp()
    SET u.fullname = user.node.name,
    u.username = user.node.login,
    u.has_2fa_enabled = user.hasTwoFactorEnabled,
    u.role = user.role,
    u.is_site_admin = user.node.isSiteAdmin,
    u.email = user.node.email,
    u.company = user.node.company,
    u.lastupdated = {UpdateTag}

    MERGE (u)-[r:MEMBER_OF]->(org)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """
    neo4j_session.run(
        query,
        OrgUrl=org_data['url'],
        OrgLogin=org_data['login'],
        UserData=user_data,
        UpdateTag=update_tag,
    )


@timeit
def sync(neo4j_session, common_job_parameters, github_api_key, github_url, organization):
    logger.info("Syncing GitHub users")
    user_data, org_data = get(github_api_key, github_url, organization)
    load_organization_users(neo4j_session, user_data, org_data, common_job_parameters['UPDATE_TAG'])
    run_cleanup_job('github_users_cleanup.json', neo4j_session, common_job_parameters)

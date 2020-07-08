import json
import logging
from string import Template

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)


def call_github_api(query, variables, token, api_url):
    """
    Calls the GitHub v4 API and executes a query
    :param query: the GraphQL query to run
    :param variables: parameters for the query
    :param token: the Oauth token for the API
    :param api_url: the URL to call for the API
    :return: query results json
    """
    headers = {'Authorization': f"token {token}"}
    response = requests.post(api_url, json={'query': query, 'variables': variables}, headers=headers)
    response.raise_for_status()
    return response.json()


def get_org_users_and_repos_with_cursor(token, api_url, organization, member_cursor=None, repo_cursor=None):
    """
    Retrieve organization members and repos from Github GraphQL API using the given member_cursor and repo_cursor
    parameters used for pagination.
    :param token: The API token as string. Must have repo:* and org:read permissions.
    :param api_url: The Github API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param member_cursor: The GraphQL cursor string (behaves like a page number) for Github member users in the given
    organization. If None, the Github API will return the first page of members.
    :param repo_cursor: The GraphQL cursor string (behaves like a page number) for Github repos in the given
    organization. If None, the Github API will return the first page of repos.
    :return: The raw response object from the requests.get().json() call.
    """
    query = """
            query($login: String!, $memberCursor: String, $repoCursor: String) {
            organization(login: $login)
                {
                    repositories(first: 100, after: $repoCursor){
                        pageInfo{
                            endCursor
                            hasNextPage
                        }
                        nodes{
                            id
                            name
                            nameWithOwner
                            primaryLanguage{
                                name
                            }
                            url
                            sshUrl
                            createdAt
                            description
                            updatedAt
                            homepageUrl
                            languages(first: 25){
                                totalCount
                                nodes{
                                    name
                                    id
                                }
                            }
                            defaultBranchRef{
                              name
                              id
                            }
                            isPrivate
                            isArchived
                            isDisabled
                            isLocked
                            owner{
                                login
                                id
                                __typename
                            }
                        }
                    }
                    membersWithRole(first:100, after: $memberCursor){
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
                rateLimit {
                    limit
                    cost
                    remaining
                    resetAt
                }
            }
            """
    gql_vars = {
        'login': organization,
        'memberCursor': member_cursor,
        'repoCursor': repo_cursor,
    }
    gql_vars_json = json.dumps(gql_vars)
    response = call_github_api(query, gql_vars_json, token, api_url)
    return response


@timeit
def get_org_users_and_repos(token, api_url, organization):
    """
    Fetches and stores each page of users and repos returned from the Github GraphQL API. We perform pagination on more
    than one resource here in order to save on API rate limits.  See
    https://developer.github.com/v4/guides/resource-limitations/#rate-limit.
    :param token: The API token as string. Must have repo:* and org:read permissions.
    :param api_url: The Github API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A dict of dicts. Has shape {'repo_pages': {<page1>, ..., <pageN>}, 'user_pages': {page1>, ..., <pageM>}}
    """
    # Track which page of data from each resource type to retrieve. If `None`, the API will return the first page.
    repo_cursor = None
    user_cursor = None

    # Whether there are additional pages to fetch for each resource.
    repo_has_next_page = True
    user_has_next_page = True

    # It is very likely that we will have an unequal number of repo pages and user pages in our Github organization. As
    # such, if we have fetched all repos but not all users, repo_has_next_page will be set to False and repo_cursor will
    # be set to None. However, user_has_next_page will still be True and the same GraphQL query will be called with
    # repo_cursor=None, causing the API to return the very first repo page again. To avoid accumulating duplicate pages,
    # we use dicts where each key is the cursor and each value is the contents of that page.
    # Fetching old pages is slightly wasteful in terms of data transfer, but there is no difference in API quota cost.
    repo_pages = {}
    user_pages = {}

    while repo_has_next_page or user_has_next_page:
        resp = get_org_users_and_repos_with_cursor(token, api_url, organization, user_cursor, repo_cursor)
        resp_repos = resp['data']['organization']['repositories']
        resp_users = resp['data']['organization']['membersWithRole']

        # Update the cursor and determine if we need to continue fetching this resource
        repo_cursor = resp_repos['pageInfo']['endCursor']
        repo_pages[repo_cursor] = resp_repos['nodes']
        if not resp_repos['pageInfo']['hasNextPage']:
            repo_has_next_page = False

        user_cursor = resp_users['pageInfo']['endCursor']
        user_pages[user_cursor] = resp_users['edges']
        if not resp_users['pageInfo']['hasNextPage']:
            user_has_next_page = False

        logger.debug(
            f"User cursor:{user_cursor}, repo cursor:{repo_cursor},"
            f"repo_has_next_page: {repo_has_next_page}, user_has_next_page: {user_has_next_page}",
        )
        logger.debug(
            f"Cost of this API call: {resp['data']['rateLimit']['cost']} unit(s),"
            f"Remaining: {resp['data']['rateLimit']['remaining']}",
        )
    return {'repo_pages': repo_pages, 'user_pages': user_pages}


@timeit
def get_github_repos(token, api_url, organization):
    """
    Gets the repo data for all repos in the organization
    :param token: the Oauth token for the API
    :param api_url: the URL to call for the API
    :param organization: the organization name to query against
    :return: list of repo json objects from GitHub
    """
    repos = []
    query = """
            query($login: String!, $after: String) {
            organization(login: $login)
                {
                    repositories(first: 100, after: $after){
                        pageInfo{
                            endCursor
                            hasNextPage
                        }
                        nodes{
                            id
                            name
                            nameWithOwner
                            primaryLanguage{
                                name
                            }
                            url
                            sshUrl
                            createdAt
                            description
                            updatedAt
                            homepageUrl
                            languages(first: 25){
                                totalCount
                                nodes{
                                    name
                                    id
                                }
                            }
                            defaultBranchRef{
                              name
                              id
                            }
                            isPrivate
                            isArchived
                            isDisabled
                            isLocked
                            owner{
                                login
                                id
                                __typename
                            }
                        }
                    }
                }
            }
            """
    has_next_page = True
    cursor = None
    while has_next_page:
        if cursor:
            variables = f'{{"login": "{organization}", "after": "{cursor}"}}'
        else:
            variables = f'{{"login": "{organization}"}}'
        results = call_github_api(query, variables, token, api_url)
        try:
            repositories = results['data']['organization']['repositories']
            if len(repositories) > 0:
                repos.extend(repositories['nodes'])
                cursor = repositories['pageInfo']['endCursor']
                has_next_page = repositories['pageInfo']['hasNextPage']
            else:
                logger.warning(f"Did not retrieve any repos for {variables}. Returned data: {results}")
                break
        except KeyError:
            logger.warning(f"Could not paginate through repos for {variables}. Returned values: {results}")
            break
    return repos


@timeit
def transform_github_repos(repos_json, github_url):
    """
    Parses the JSON returned from GitHub API to create data for graph ingestion
    :param repos_json: the list of individual repository nodes from GitHub
    :param github_url: optional prefix to append to id for ingesting multiple organizations
    :return: Dict containing the repos, repo->language mapping, and owners->repo mapping
    """
    repos = []
    repo_languages = []
    repo_owners = []
    for repo in repos_json:
        # github ids as provided is only unique per instance. Include the URL to make unique for all ids
        githubid = f"{github_url}:{repo['id']}"
        fullname = repo['nameWithOwner']
        if repo['languages']['totalCount'] > 0:
            for language in repo['languages']['nodes']:
                repo_languages.append({
                    'repoid': githubid,
                    'language': language['name'],
                    'languageid': language['name'],
                })
        defaultbranch = None
        defaultbranchid = None
        defaultbranchref = repo.get('defaultBranchRef')
        if defaultbranchref:
            defaultbranch = defaultbranchref['name']
            defaultbranchid = f"{github_url}:{defaultbranchref['id']}"
        primarylanguage = None
        primarylanguageref = repo.get('primaryLanguage')
        if primarylanguageref:
            primarylanguage = primarylanguageref.get('name')
        sshurl = repo.get('sshUrl')
        if sshurl:
            giturl = sshurl.replace("/", ":").replace("git@", "git://")
        else:
            giturl = None
        repos.append({
            'id': githubid,
            'createdat': repo.get('createdAt'),
            'name': repo.get('name'),
            'fullname': fullname,
            'description': repo.get('description'),
            'primarylanguage': primarylanguage,
            'homepage': repo.get('homepageUrl'),
            'defaultbranch': defaultbranch,
            'defaultbranchid': defaultbranchid,
            'private': repo.get('isPrivate'),
            'disabled': repo.get('isDisabled'),
            'archived': repo.get('isArchived'),
            'locked': repo.get('isLocked'),
            'giturl': giturl,
            'url': repo.get('url'),
            'sshurl': sshurl,
            'updatedat': repo.get('updatedAt'),
        })
        ownerid = f"{github_url}:{repo['owner']['id']}"
        repo_owners.append({
            'repoid': githubid,
            'owner': repo['owner']['login'],
            'ownerid': ownerid,
            'type': repo['owner']['__typename'],
        })
    results = {
        'repos': repos,
        'repo_languages': repo_languages,
        'repo_owners': repo_owners,
    }
    return results


@timeit
def load_github_repos(session, update_tag, repo_data):
    """
    Ingest the GitHub repository information
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_data: repository data objects
    :return: None
        """
    ingest_repo = """
    UNWIND {RepoData} as repository
    MERGE (repo:GitHubRepository{id: repository.id})
    ON CREATE SET repo.firstseen = timestamp(), repo.createdat = repository.createdat
    set repo.name = repository.name, repo.fullname = repository.fullname,
    repo.description = repository.description, repo.primarylanguage = repository.primarylanguage,
    repo.homepage = repository.homepage, repo.defaultbranch = repository.defaultbranch,
    repo.defaultbranchid = repository.defaultbranchid, repo.private = repository.private,
    repo.disabled = repository.disabled, repo.archived = repository.archived,
    repo.locked = repository.locked, repo.giturl = repository.giturl, repo.url = repository.url,
    repo.sshurl = repository.sshurl, repo.updatedat = repository.updatedat,
    repo.lastupdated = {UpdateTag}
    WITH repo
    MERGE (branch:GitHubBranch{id: repo.defaultbranchid})
    ON CREATE SET branch.firstseen = timestamp()
    SET branch.name = repo.defaultbranch, branch.lastupdated = {UpdateTag}
    WITH repo, branch
    MERGE (repo)-[r:BRANCH]->(branch)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = r.UpdateTag;"""

    session.run(
        ingest_repo,
        RepoData=repo_data,
        UpdateTag=update_tag,
    )


@timeit
def load_github_owners(session, update_tag, repo_owners):
    """
    Ingest the relationships for repo owners
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_owners: list of owner to repo mappings
    :return: None
    """
    for owner in repo_owners:
        ingest_owner_template = Template("""MERGE (user:$account_type{id: {Id}})
            ON CREATE SET user.firstseen = timestamp()
            SET user.username = {UserName}, user.lastupdated = {UpdateTag}
            WITH user
            MATCH (repo:GitHubRepository{id: {RepoId}})
            MERGE (user)<-[r:OWNER]-(repo)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {UpdateTag}""")

        account_type = {'User': "GitHubUser", 'Organization': "GitHubOrganization"}

        session.run(
            ingest_owner_template.safe_substitute(account_type=account_type[owner['type']]),
            Id=owner['ownerid'],
            UserName=owner['owner'],
            RepoId=owner['repoid'],
            UpdateTag=update_tag,
        )


@timeit
def load_github_languages(session, update_tag, repo_languages):
    """
    Ingest the relationships for repo languages
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_languages: list of language to repo mappings
    :return: None
    """
    ingest_languages = """Unwind {Languages} as lang
        MERGE (language:ProgrammingLanguage{id: lang.languageid})
        ON CREATE SET language.firstseen = timestamp(), language.name = lang.language
        SET language.lastupdated = {UpdateTag}
        WITH language, lang
        MATCH (repo:GitHubRepository{id: lang.repoid})
        MERGE (language)<-[r:LANGUAGE]-(repo)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}"""

    session.run(
        ingest_languages,
        Languages=repo_languages,
        UpdateTag=update_tag,
    )


@timeit
def sync_github(neo4j_session, common_job_parameters, github_api_key, github_url, organization):
    """
        Performs the sequential tasks to collect, transform, and sync github data
        :param neo4j_session: Neo4J session for database interface
        :param common_job_parameters: Common job parameters containing UPDATE_TAG
        :param github_api_key: The API key to access the GitHub v4 API
        :param github_url: The URL for the GitHub v4 endpoint to use
        :param organization: The organization to query GitHub for
        :return: None
    """
    repos_json = get_github_repos(github_api_key, github_url, organization)
    repo_data = transform_github_repos(repos_json, github_url)

    load_github_repos(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repos'])
    load_github_owners(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_owners'])
    load_github_languages(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_languages'])

import logging
from string import Template

from cartography.util import timeit
from cartography.intel.github.util import fetch_all


logger = logging.getLogger(__name__)

GITHUB_ORG_REPOS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            repositories(first: 100, after: $cursor){
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


@timeit
def get(token, api_url, organization):
    """
    Retrieve a list of repos from a Github organization as described in
    https://docs.github.com/en/graphql/reference/objects#repository.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A list of dicts representing repos. See #TODO for full datashape
    """
    return fetch_all(token, api_url, organization, GITHUB_ORG_REPOS_PAGINATED_GRAPHQL, 'repositories', 'nodes')


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
def load_github_languages(session, update_tag, repo_languages):
    """
    Ingest the relationships for repo languages
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_languages: list of language to repo mappings
    :return: Nothing
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
def load_github_owners(session, update_tag, repo_owners):
    """
    Ingest the relationships for repo owners
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_owners: list of owner to repo mappings
    :return: Nothing
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
def sync(neo4j_session, common_job_parameters, github_api_key, github_url, organization):
    """
    Performs the sequential tasks to collect, transform, and sync github data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param github_api_key: The API key to access the GitHub v4 API
    :param github_url: The URL for the GitHub v4 endpoint to use
    :param organization: The organization to query GitHub for
    :return: Nothing
    """
    repos_json = get(github_api_key, github_url, organization)
    repo_data = transform_github_repos(repos_json, github_url)
    load_github_repos(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repos'])
    load_github_owners(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_owners'])
    load_github_languages(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_languages'])

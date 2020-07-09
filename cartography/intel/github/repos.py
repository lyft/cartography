import logging
from string import Template

from cartography.intel.github.util import fetch_all
from cartography.util import timeit


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
                        url
                        login
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
    :return: A list of dicts representing repos. See tests.data.github.repos for data shape.
    """
    return fetch_all(token, api_url, organization, GITHUB_ORG_REPOS_PAGINATED_GRAPHQL, 'repositories', 'nodes')


def transform_github_repos(repos_json):
    """
    Parses the JSON returned from GitHub API to create data for graph ingestion
    :param repos_json: the list of individual repository nodes from GitHub
    :return: Dict containing the repos, repo->language mapping, and owners->repo mapping
    """
    transformed_repo_list = []
    transformed_repo_languages = []
    transformed_repo_owners = []
    for repo_object in repos_json:
        _transform_repo_languages(repo_object['url'], repo_object, transformed_repo_languages)
        _transform_repo_objects(repo_object, transformed_repo_list)
        _transform_repo_owners(repo_object['owner']['url'], repo_object, transformed_repo_owners)
    results = {
        'repos': transformed_repo_list,
        'repo_languages': transformed_repo_languages,
        'repo_owners': transformed_repo_owners,
    }
    return results


def _create_default_branch_id(repo_url, default_branch_ref_id):
    """
    Return a unique node id for the defaultBranchId using the given repo_url and default_branch_ref_id.
    This ensures that default branches for each GitHub repo are unique nodes in the graph.
    """
    return f"{repo_url}:{default_branch_ref_id}"


def _create_git_url_from_ssh_url(ssh_url):
    """
    Return a git:// URL from the given ssh_url
    """
    return ssh_url.replace("/", ":").replace("git@", "git://")


def _transform_repo_objects(input_repo_object, out_repo_list):
    default_branch_id = _create_default_branch_id(input_repo_object['url'], input_repo_object['defaultBranchRef']['id'])
    # Create a git:// URL from the given SSH URL
    ssh_url = input_repo_object.get('sshUrl')
    git_url = _create_git_url_from_ssh_url(ssh_url) if ssh_url else None
    out_repo_list.append({
        'id': input_repo_object['url'],
        'createdat': input_repo_object['createdAt'],
        'name': input_repo_object['name'],
        'fullname': input_repo_object['nameWithOwner'],
        'description': input_repo_object['description'],
        'primarylanguage': input_repo_object['primaryLanguage'],
        'homepage': input_repo_object['homepageUrl'],
        'defaultbranch': input_repo_object['defaultBranchRef']['name'],
        'defaultbranchid': default_branch_id,
        'private': input_repo_object['isPrivate'],
        'disabled': input_repo_object['isDisabled'],
        'archived': input_repo_object['isArchived'],
        'locked': input_repo_object['isLocked'],
        'giturl': git_url,
        'url': input_repo_object['url'],
        'sshurl': ssh_url,
        'updatedat': input_repo_object['updatedAt'],
    })


def _transform_repo_owners(owner_id, repo, repo_owners):
    repo_owners.append({
        'repo_id': repo['url'],
        'owner': repo['owner']['login'],
        'owner_id': owner_id,
        'type': repo['owner']['__typename'],
    })


def _transform_repo_languages(repo_url, repo, repo_languages):
    if repo['languages']['totalCount'] > 0:
        for language in repo['languages']['nodes']:
            repo_languages.append({
                'repo_id': repo_url,
                'language_name': language['name'],
            })


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
    ON CREATE SET repo.firstseen = timestamp(),
    repo.createdat = repository.createdat

    SET repo.name = repository.name,
    repo.fullname = repository.fullname,
    repo.description = repository.description,
    repo.primarylanguage = repository.primarylanguage.name,
    repo.homepage = repository.homepage,
    repo.defaultbranch = repository.defaultbranch,
    repo.defaultbranchid = repository.defaultbranchid,
    repo.private = repository.private,
    repo.disabled = repository.disabled,
    repo.archived = repository.archived,
    repo.locked = repository.locked,
    repo.giturl = repository.giturl,
    repo.url = repository.url,
    repo.sshurl = repository.sshurl,
    repo.updatedat = repository.updatedat,
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
    ingest_languages = """
        UNWIND {Languages} as lang

        MERGE (pl:ProgrammingLanguage{id: lang.language_name})
        ON CREATE SET pl.firstseen = timestamp(),
        pl.name = lang.language_name
        SET pl.lastupdated = {UpdateTag}
        WITH pl, lang

        MATCH (repo:GitHubRepository{id: lang.repo_id})
        MERGE (pl)<-[r:LANGUAGE]-(repo)
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
        ingest_owner_template = Template("""
            MERGE (user:$account_type{id: {Id}})
            ON CREATE SET user.firstseen = timestamp()
            SET user.username = {UserName},
            user.lastupdated = {UpdateTag}
            WITH user

            MATCH (repo:GitHubRepository{id: {RepoId}})
            MERGE (user)<-[r:OWNER]-(repo)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {UpdateTag}""")

        account_type = {'User': "GitHubUser", 'Organization': "GitHubOrganization"}

        session.run(
            ingest_owner_template.safe_substitute(account_type=account_type[owner['type']]),
            Id=owner['owner_id'],
            UserName=owner['owner'],
            RepoId=owner['repo_id'],
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
    repo_data = transform_github_repos(repos_json)
    load_github_repos(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repos'])
    load_github_owners(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_owners'])
    load_github_languages(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_languages'])

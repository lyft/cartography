import logging
from string import Template

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from cartography.intel.github.util import fetch_all
from cartography.util import run_cleanup_job
from cartography.util import timeit


logger = logging.getLogger(__name__)

GITHUB_ORG_REPOS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            url
            login
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
                    collaborators(affiliation: OUTSIDE, first: 100) {
                        edges {
                            permission
                        }
                        nodes {
                            url
                            login
                            name
                            email
                            company
                        }
                    }
                    requirements:object(expression: "HEAD:requirements.txt") {
                        ... on Blob {
                            text
                        }
                    }
                }
            }
        }
    }
    """
# Note: In the above query, `HEAD` references the default branch.
# See https://stackoverflow.com/questions/48935381/github-graphql-api-default-branch-in-repository


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
    # TODO: link the Github organization to the repositories
    repos, _ = fetch_all(token, api_url, organization, GITHUB_ORG_REPOS_PAGINATED_GRAPHQL, 'repositories', 'nodes')
    return repos


def transform(repos_json):
    """
    Parses the JSON returned from GitHub API to create data for graph ingestion
    :param repos_json: the list of individual repository nodes from GitHub. See tests.data.github.repos.GET_REPOS for
    data shape.
    :return: Dict containing the repos, repo->language mapping, owners->repo mapping, outside collaborators->repo
    mapping, and Python requirements files (if any) in a repo.
    """
    transformed_repo_list = []
    transformed_repo_languages = []
    transformed_repo_owners = []
    # See https://docs.github.com/en/graphql/reference/enums#repositorypermission
    transformed_collaborators = {'ADMIN': [], 'MAINTAIN': [], 'READ': [], 'TRIAGE': [], 'WRITE': []}
    transformed_requirements_files = []
    for repo_object in repos_json:
        _transform_repo_languages(repo_object['url'], repo_object, transformed_repo_languages)
        _transform_repo_objects(repo_object, transformed_repo_list)
        _transform_repo_owners(repo_object['owner']['url'], repo_object, transformed_repo_owners)
        _transform_collaborators(repo_object['collaborators'], repo_object['url'], transformed_collaborators)
        _transform_python_requirements(repo_object, transformed_requirements_files)
    results = {
        'repos': transformed_repo_list,
        'repo_languages': transformed_repo_languages,
        'repo_owners': transformed_repo_owners,
        'repo_collaborators': transformed_collaborators,
        'python_requirements': transformed_requirements_files,
    }
    return results


def _create_default_branch_id(repo_url, default_branch_ref_id):
    """
    Return a unique node id for a repo's defaultBranchId using the given repo_url and default_branch_ref_id.
    This ensures that default branches for each GitHub repo are unique nodes in the graph.
    """
    return f"{repo_url}:{default_branch_ref_id}"


def _create_git_url_from_ssh_url(ssh_url):
    """
    Return a git:// URL from the given ssh_url
    """
    return ssh_url.replace("/", ":").replace("git@", "git://")


def _transform_repo_objects(input_repo_object, out_repo_list):
    """
    Performs data transforms including creating necessary IDs for unique nodes in the graph related to GitHub repos,
    their default branches, and languages.
    :param input_repo_object: A repository node from GitHub; see tests.data.github.repos.GET_REPOS for data shape.
    :param out_repo_list: Out-param to append transformed repos to.
    :return: Nothing
    """
    # Create a unique ID for a GitHubBranch node representing the default branch of this repo object.
    dbr = input_repo_object['defaultBranchRef']
    default_branch_name = dbr['name'] if dbr else None
    default_branch_id = _create_default_branch_id(input_repo_object['url'], dbr['id']) if dbr else None

    # Create a git:// URL from the given SSH URL, if it exists.
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
        'defaultbranch': default_branch_name,
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
    """
    Helper function to transform repo owners.
    :param owner_id: The URL of the owner object (either of type Organization or User).
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_owners: Output array to append transformed results to.
    :return: Nothing.
    """
    repo_owners.append({
        'repo_id': repo['url'],
        'owner': repo['owner']['login'],
        'owner_id': owner_id,
        'type': repo['owner']['__typename'],
    })


def _transform_repo_languages(repo_url, repo, repo_languages):
    """
    Helper function to transform the languages in a GitHub repo.
    :param repo_url: The URL of the repo.
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_languages: Output array to append transformed results to.
    :return: Nothing.
    """
    if repo['languages']['totalCount'] > 0:
        for language in repo['languages']['nodes']:
            repo_languages.append({
                'repo_id': repo_url,
                'language_name': language['name'],
            })


def _transform_collaborators(collaborators, repo_url, transformed_collaborators):
    """
    Performs data adjustments for outside collaborators in a GitHub repo.
    Output data shape = [{permission, repo_url, url (the user's URL), login, name}, ...]
    :param collaborators: See cartography.tests.data.github.repos for data shape.
    :param repo_url: The URL of the GitHub repo.
    :param transformed_collaborators: Output dict. Data shape =
    {'ADMIN': [{ user }, ...], 'MAINTAIN': [{ user }, ...], 'READ': [ ... ], 'TRIAGE': [ ... ], 'WRITE': [ ... ]}
    :return: Nothing.
    """
    # `collaborators` is sometimes None
    if collaborators:
        for idx, user in enumerate(collaborators['nodes']):
            user_permission = collaborators['edges'][idx]['permission']
            user['repo_url'] = repo_url
            transformed_collaborators[user_permission].append(user)


def _transform_python_requirements(repo_object, out_requirements_files):
    """
    Performs data transformations for the requirements.txt files in a GitHub repo, if available.
    :param repo_object: The repo object.
    :param out_requirements_files: Output array to append transformed results to.
    :return: Nothing.
    """
    req_file_contents = repo_object['requirements']
    if req_file_contents and req_file_contents.get('text'):
        text_contents = req_file_contents['text']

        parsed_list = []
        for line in text_contents.split("\n"):
            try:
                # Remove trailing comments and extra whitespace
                line = line.partition('#')[0].strip()
                req = Requirement(line)
                parsed_list.append(req)
            except InvalidRequirement as e:
                logger.info(
                    f"Failed to parse line \"{line}\" in repo {repo_object['url']}'s requirements.txt; skipping line. "
                    f"Details: {e}. This is probably ok since we don't support all ways to specify Python "
                    f"requirements.",
                )
                continue

        for req in parsed_list:
            pinned_version = None
            if len(req.specifier) == 1:
                specifier = next(iter(req.specifier))
                if specifier.operator == '==':
                    pinned_version = specifier.version

            # Set `spec` to a default value. Example values for str(req.specifier): "<4.0,>=3.0" or "==1.0.0".
            spec = str(req.specifier)
            # Set spec to `None` instead of empty string so that the Neo4j driver will leave the library.specifier field
            # undefined. As convention, we prefer undefined values over empty strings in the graph.
            if spec == '':
                spec = None

            canon_name = canonicalize_name(req.name)
            requirement_id = f"{canon_name}|{pinned_version}" if pinned_version else canon_name

            out_requirements_files.append({
                "id": requirement_id,
                "name": canon_name,
                "specifier": spec,
                "version": pinned_version,
                "repo_url": repo_object['url'],
            })


@timeit
def load_github_repos(neo4j_session, update_tag, repo_data):
    """
    Ingest the GitHub repository information
    :param neo4j_session: Neo4J session object for server communication
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
    WHERE repo.defaultbranch IS NOT NULL AND repo.defaultbranchid IS NOT NULL
    MERGE (branch:GitHubBranch{id: repo.defaultbranchid})
    ON CREATE SET branch.firstseen = timestamp()
    SET branch.name = repo.defaultbranch,
    branch.lastupdated = {UpdateTag}

    MERGE (repo)-[r:BRANCH]->(branch)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = r.UpdateTag
    """
    neo4j_session.run(
        ingest_repo,
        RepoData=repo_data,
        UpdateTag=update_tag,
    )


@timeit
def load_github_languages(neo4j_session, update_tag, repo_languages):
    """
    Ingest the relationships for repo languages
    :param neo4j_session: Neo4J session object for server communication
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

    neo4j_session.run(
        ingest_languages,
        Languages=repo_languages,
        UpdateTag=update_tag,
    )


@timeit
def load_github_owners(neo4j_session, update_tag, repo_owners):
    """
    Ingest the relationships for repo owners
    :param neo4j_session: Neo4J session object for server communication
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

        neo4j_session.run(
            ingest_owner_template.safe_substitute(account_type=account_type[owner['type']]),
            Id=owner['owner_id'],
            UserName=owner['owner'],
            RepoId=owner['repo_id'],
            UpdateTag=update_tag,
        )


@timeit
def load_collaborators(neo4j_session, update_tag, collaborators):
    query = Template("""
    UNWIND {UserData} as user

    MERGE (u:GitHubUser{id: user.url})
    ON CREATE SET u.firstseen = timestamp()
    SET u.fullname = user.name,
    u.username = user.login,
    u.permission = user.permission,
    u.email = user.email,
    u.company = user.company,
    u.lastupdated = {UpdateTag}

    WITH u, user
    MATCH (repo:GitHubRepository{id: user.repo_url})
    MERGE (repo)<-[o:$rel_label]-(u)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = {UpdateTag}
    """)
    for collab_type in collaborators.keys():
        relationship_label = f"OUTSIDE_COLLAB_{collab_type}"
        neo4j_session.run(
            query.safe_substitute(rel_label=relationship_label),
            UserData=collaborators[collab_type],
            UpdateTag=update_tag,
        )


@timeit
def load(neo4j_session, common_job_parameters, repo_data):
    load_github_repos(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repos'])
    load_github_owners(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_owners'])
    load_github_languages(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_languages'])
    load_collaborators(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_collaborators'])
    load_python_requirements(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['python_requirements'])


@timeit
def load_python_requirements(neo4j_session, update_tag, requirements_objects):
    query = """
    UNWIND {Requirements} AS req
        MERGE (lib:PythonLibrary:Dependency{id: req.id})
        ON CREATE SET lib.firstseen = timestamp(),
        lib.name = req.name
        SET lib.lastupdated = {UpdateTag},
        lib.version = req.version

        WITH lib, req
        MATCH (repo:GitHubRepository{id: req.repo_url})
        MERGE (repo)-[r:REQUIRES]->(lib)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag},
        r.specifier = req.specifier
    """
    neo4j_session.run(
        query,
        Requirements=requirements_objects,
        UpdateTag=update_tag,
    )


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
    logger.info("Syncing GitHub repos")
    repos_json = get(github_api_key, github_url, organization)
    repo_data = transform(repos_json)
    load(neo4j_session, common_job_parameters, repo_data)
    run_cleanup_job('github_repos_cleanup.json', neo4j_session, common_job_parameters)

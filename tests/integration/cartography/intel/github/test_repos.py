import cartography.intel.github
import tests.data.github.repos


TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {'UPDATE_TAG': TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    repo_data = cartography.intel.github.repos.transform(tests.data.github.repos.GET_REPOS)
    cartography.intel.github.repos.load(
        neo4j_session,
        TEST_JOB_PARAMS,
        repo_data,
    )


def test_transform_and_load_repositories(neo4j_session):
    """
    Test that we can correctly transform and load GitHubRepository nodes to Neo4j.
    """
    repositories_res = tests.data.github.repos.GET_REPOS
    repos_data = cartography.intel.github.repos.transform(repositories_res)
    cartography.intel.github.repos.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repos'],
    )
    nodes = neo4j_session.run(
        "MATCH(repo:GitHubRepository) RETURN repo.id",
    )
    actual_nodes = {n['repo.id'] for n in nodes}
    expected_nodes = {
        "https://github.com/example_org/sample_repo",
        "https://github.com/example_org/SampleRepo2",
        "https://github.com/lyft/cartography",
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_owners(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    """
    repositories_res = tests.data.github.repos.GET_REPOS
    repos_data = cartography.intel.github.repos.transform(repositories_res)
    cartography.intel.github.repos.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_owners'],
    )
    nodes = neo4j_session.run(
        "MATCH(owner:GitHubOrganization) RETURN owner.id",
    )
    actual_nodes = {n['owner.id'] for n in nodes}
    expected_nodes = {
        'https://github.com/example_org',
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_languages(neo4j_session):
    """
    Ensure we can transform and load GitHub repository languages nodes.
    """
    repositories_res = tests.data.github.repos.GET_REPOS
    repos_data = cartography.intel.github.repos.transform(repositories_res)
    cartography.intel.github.repos.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_languages'],
    )
    nodes = neo4j_session.run(
        "MATCH(pl:ProgrammingLanguage) RETURN pl.id",
    )
    actual_nodes = {n['pl.id'] for n in nodes}
    expected_nodes = {
        'Python', 'Makefile',
    }
    assert actual_nodes == expected_nodes


def test_repository_to_owners(neo4j_session):
    """
    Ensure that repositories are connected to owners.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(owner:GitHubOrganization)<-[:OWNER]-(repo:GitHubRepository{id:{RepositoryId}})
    RETURN owner.username, repo.id, repo.name
    """
    expected_repository_id = 'https://github.com/example_org/SampleRepo2'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['owner.username'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'example_org',
            'https://github.com/example_org/SampleRepo2',
            'SampleRepo2',
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_branches(neo4j_session):
    """
    Ensure that repositories are connected to branches.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(branch:GitHubBranch)<-[:BRANCH]-(repo:GitHubRepository{id:{RepositoryId}})
    RETURN branch.name, repo.id, repo.name
    """
    expected_repository_id = 'https://github.com/example_org/sample_repo'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['branch.name'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'master',
            'https://github.com/example_org/sample_repo',
            'sample_repo',
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_languages(neo4j_session):
    """
    Ensure that repositories are connected to languages.
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)
    query = """
    MATCH(lang:ProgrammingLanguage)<-[:LANGUAGE]-(repo:GitHubRepository{id:{RepositoryId}})
    RETURN lang.name, repo.id, repo.name
    """
    expected_repository_id = 'https://github.com/example_org/SampleRepo2'
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = {
        (
            n['lang.name'],
            n['repo.id'],
            n['repo.name'],
        ) for n in nodes
    }

    expected_nodes = {
        (
            'Python',
            'https://github.com/example_org/SampleRepo2',
            'SampleRepo2',
        ),
    }
    assert actual_nodes == expected_nodes


def test_repository_to_collaborators(neo4j_session):
    _ensure_local_neo4j_has_test_data(neo4j_session)
    nodes = neo4j_session.run("""
    MATCH (repo:GitHubRepository{name:"cartography"})<-[:OUTSIDE_COLLAB_WRITE]-(user:GitHubUser)
    RETURN count(user.username) as collab_count
    """)
    actual_nodes = {n['collab_count'] for n in nodes}
    expected_nodes = {5}
    assert actual_nodes == expected_nodes


def test_pinned_python_library_to_repo(neo4j_session):
    """
    Ensure that repositories are connected to pinned Python libraries.
    Create the path (:RepoA)-[:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary with a specifier (RepoA).
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Note: don't query for relationship attributes in code that needs to be fast.
    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography|0.1.0'})
    WHERE lib.version = "0.1.0"
    RETURN count(repo) as repo_count
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {n['repo_count'] for n in nodes}
    expected_nodes = {1}
    assert actual_nodes == expected_nodes


def test_upinned_python_library_to_repo(neo4j_session):
    """
    Ensure that repositories are connected to un-pinned Python libraries.
    That is, create the path
    (:RepoA)-[r:REQUIRES{specifier:"0.1.0"}]->(:PythonLibrary{'Cartography'})<-[:REQUIRES]-(:RepoB),
    and verify that exactly 1 repo is connected to the PythonLibrary without using a pinned specifier (RepoB).
    """
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Note: don't query for relationship attributes in code that needs to be fast.
    query = """
    MATCH (repo:GitHubRepository)-[r:REQUIRES]->(lib:PythonLibrary{id:'cartography'})
    WHERE r.specifier is NULL
    RETURN count(repo) as repo_count
    """
    nodes = neo4j_session.run(query)
    actual_nodes = {n['repo_count'] for n in nodes}
    expected_nodes = {1}
    assert actual_nodes == expected_nodes

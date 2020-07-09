import cartography.intel.github
import tests.data.github.repos


TEST_UPDATE_TAG = 123456789
TEST_GITHUB_URL = "https://fake.github.net/graphql/"


def _ensure_local_neo4j_has_test_repositories_data(neo4j_session):
    cartography.intel.github.repos.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.repos.TRANSFORMED_REPOS_DATA['repos'],
    )


def _ensure_local_neo4j_has_test_owners_data(neo4j_session):
    cartography.intel.github.repos.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.repos.TRANSFORMED_REPOS_DATA['repo_owners'],
    )


def _ensure_local_neo4j_has_test_languages_data(neo4j_session):
    cartography.intel.github.repos.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.repos.TRANSFORMED_REPOS_DATA['repo_languages'],
    )


def test_transform_and_load_repositories(neo4j_session):
    """
    Test that we can correctly transform and load GitHubRepository nodes to Neo4j.
    """
    repositories_res = tests.data.github.repos.GET_REPOS
    repos_data = cartography.intel.github.repos.transform_github_repos(repositories_res)
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
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_owners(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    """
    repositories_res = tests.data.github.repos.GET_REPOS
    repos_data = cartography.intel.github.repos.transform_github_repos(repositories_res)
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
    repos_data = cartography.intel.github.repos.transform_github_repos(repositories_res)
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
        'Python',
    }
    assert actual_nodes == expected_nodes


def test_repository_to_owners(neo4j_session):
    """
    Ensure that repositories are connected to owners.
    """
    _ensure_local_neo4j_has_test_repositories_data(neo4j_session)
    _ensure_local_neo4j_has_test_owners_data(neo4j_session)
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
    _ensure_local_neo4j_has_test_repositories_data(neo4j_session)
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
    _ensure_local_neo4j_has_test_repositories_data(neo4j_session)
    _ensure_local_neo4j_has_test_languages_data(neo4j_session)
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

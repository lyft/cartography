import cartography.intel.github.github
import tests.data.github.github


TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_repositories_data(neo4j_session):
    cartography.intel.github.github.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.github.TRANSFORMED_REPOS_DATA['repos'],
    )


def _ensure_local_neo4j_has_test_owners_data(neo4j_session):
    cartography.intel.github.github.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.github.TRANSFORMED_REPOS_DATA['repo_owners'],
    )


def _ensure_local_neo4j_has_test_languages_data(neo4j_session):
    cartography.intel.github.github.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.github.github.TRANSFORMED_REPOS_DATA['repo_languages'],
    )


def test_transform_and_load_repositories(neo4j_session):
    """
    Test that we can correctly transform and load GitHubRepository nodes to Neo4j.
    """
    repositories_res = tests.data.github.github.API_RESPONSE
    repos_data = cartography.intel.github.github.transform_github_repos(repositories_res)
    cartography.intel.github.github.load_github_repos(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repos'],
    )

    query = """
    MATCH(repo:GitHubRepository{id:{RepositoryId}})
    RETURN
    repo.id,
    repo.createdat,
    repo.name,
    repo.fullname,
    repo.description,
    repo.primarylanguage,
    repo.homepage,
    repo.defaultbranch,
    repo.defaultbranchid,
    repo.private,
    repo.disabled,
    repo.archived,
    repo.locked,
    repo.giturl,
    repo.url,
    repo.sshurl,
    repo.updatedat
    """
    expected_repository_id = 'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg=='
    nodes = neo4j_session.run(
        query,
        RepositoryId=expected_repository_id,
    )
    actual_nodes = list([
        (
            n['repo.id'],
            n['repo.createdat'],
            n['repo.name'],
            n['repo.fullname'],
            n['repo.description'],
            n['repo.primarylanguage'],
            n['repo.homepage'],
            n['repo.defaultbranch'],
            n['repo.defaultbranchid'],
            n['repo.private'],
            n['repo.disabled'],
            n['repo.archived'],
            n['repo.locked'],
            n['repo.giturl'],
            n['repo.url'],
            n['repo.sshurl'],
            n['repo.updatedat'],
        ) for n in nodes
    ])
    expected_nodes = list([
        (
            expected_repository_id,
            '2018-06-20T00:53:01Z',
            'pythontestlib',
            'fake/pythontestlib',
            'Fake service for testing',
            'Python',
            None,
            'master',
            'https://fake.github.net/graphql/:MDM6UmVmMTY6bWFzdGVy',
            True,
            False,
            False,
            False,
            'git://fake.github.net:pythontestlib.git',
            'https://fake.github.net/pythontestlib',
            'git@fake.github.net/pythontestlib.git',
            '2019-10-07T21:49:08Z',
        ),
    ])
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_owners(neo4j_session):
    """
    Ensure we can transform and load GitHub repository owner nodes.
    """
    repositories_res = tests.data.github.github.API_RESPONSE
    repos_data = cartography.intel.github.github.transform_github_repos(repositories_res)
    cartography.intel.github.github.load_github_owners(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_owners'],
    )

    query = """
    MATCH(owner:GitHubOrganization{id:{OwnerId}})
    RETURN owner.id, owner.username
    """
    expected_owner_id = 'https://fake.github.net/graphql/:MDAxOk9yZ2FuaXphdGlvbjE='
    nodes = neo4j_session.run(query, OwnerId=expected_owner_id)

    actual_nodes = list([
        (
            n['owner.id'],
            n['owner.username'],
        ) for n in nodes
    ])

    expected_nodes = list([
        (
            'https://fake.github.net/graphql/:MDAxOk9yZ2FuaXphdGlvbjE=',
            'fake',
        ),
    ])
    assert actual_nodes == expected_nodes


def test_transform_and_load_repository_languages(neo4j_session):
    """
    Ensure we can transform and load GitHub repository languages nodes.
    """
    repositories_res = tests.data.github.github.API_RESPONSE
    repos_data = cartography.intel.github.github.transform_github_repos(repositories_res)
    cartography.intel.github.github.load_github_languages(
        neo4j_session,
        TEST_UPDATE_TAG,
        repos_data['repo_languages'],
    )

    query = """
    MATCH(lang:ProgrammingLanguage{id:{LanguageId}})
    RETURN lang.id, lang.language
    """
    expected_language_id = 'Makefile'
    nodes = neo4j_session.run(query, LanguageId=expected_language_id)

    actual_nodes = list([
        (
            n['lang.id'],
            n['lang.language'],
        ) for n in nodes
    ])

    expected_nodes = list([
        (
            'Makefile',
            'Makefile',
        ),
    ])
    assert actual_nodes == expected_nodes


def test_repository_to_owners(neo4j_session):
    """
    Ensure that repositories are connected to owners.
    """
    _ensure_local_neo4j_has_test_repositories_data(neo4j_session)
    _ensure_local_neo4j_has_test_owners_data(neo4j_session)
    query = """
    MATCH(owner:GitHubOrganization)-[:OWNER]->(repo:GitHubRepository{id:{RepositoryId}})
    RETURN owner.username, repo.id, repo.name
    """
    expected_repository_id = 'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg=='
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
            'fake',
            'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==',
            'pythontestlib',
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
    expected_repository_id = 'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg=='
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
            'MakeFile',
            'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==',
            'pythontestlib',
        ),
        (
            'Python',
            'https://fake.github.net/graphql/:MDEwOlJlcG9zaXRvcnkxNg==',
            'pythontestlib',
        ),
    }
    assert actual_nodes == expected_nodes

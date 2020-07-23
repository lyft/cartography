import cartography.intel.github.users
import tests.data.github.users

TEST_UPDATE_TAG = 123456789


def test_load_github_organization_users(neo4j_session):
    cartography.intel.github.users.load_organization_users(
        neo4j_session,
        tests.data.github.users.GITHUB_USER_DATA,
        tests.data.github.users.GITHUB_ORG_DATA,
        TEST_UPDATE_TAG,
    )

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id, g.role;
        """,
    )
    expected_nodes = {
        ("https://example.com/hjsimpson", 'MEMBER'),
        ("https://example.com/mbsimpson", 'ADMIN'),
    }
    actual_nodes = {
        (
            n['g.id'],
            n['g.role'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure users are connected to the expected organization
    nodes = neo4j_session.run(
        """
        MATCH(user:GitHubUser)-[:MEMBER_OF]->(org:GitHubOrganization)
        RETURN user.id, org.id
        """,
    )
    actual_nodes = {
        (
            n['user.id'],
            n['org.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            'https://example.com/hjsimpson',
            'https://example.com/my_org',
        ), (
            'https://example.com/mbsimpson',
            'https://example.com/my_org',
        ),
    }
    assert actual_nodes == expected_nodes

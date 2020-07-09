import cartography.intel.github.users
from tests.data.github.users import GITHUB_USER_DATA

TEST_UPDATE_TAG = 123456789


def test_load_github_users(neo4j_session):
    cartography.intel.github.users.load(
        neo4j_session,
        GITHUB_USER_DATA,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/hjsimpson",
        "/mbsimpson",
    }

    nodes = neo4j_session.run(
        """
        MATCH (g:GitHubUser) RETURN g.id;
        """,
    )
    actual_nodes = {n['g.id'] for n in nodes}

    assert actual_nodes == expected_nodes

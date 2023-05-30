import cartography.intel.hexnode.users
import tests.data.hexnode.users


COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": 123456789,
    "TENANT": 'FooBar',
}


def test_load_hexnode_users(neo4j_session):

    cartography.intel.hexnode.users.load(
        neo4j_session,
        tests.data.hexnode.users.HEXNODE_USERS,
        COMMON_JOB_PARAMETERS,
    )

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:HexnodeUser) RETURN e.id, e.email, e.domain;
        """,
    )
    expected_nodes = {
        (1, None, 'local'),
        (2, 'john.doe@domain.tld', 'gsuite'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.email'],
            n['e.domain'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

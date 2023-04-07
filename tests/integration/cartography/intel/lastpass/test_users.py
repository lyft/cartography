import cartography.intel.lastpass.users
import tests.data.lastpass.users


TEST_UPDATE_TAG = 123456789


def test_load_lastpass_users(neo4j_session):

    data = tests.data.lastpass.users.LASTPASS_USERS
    formatted_data = cartography.intel.lastpass.users.transform(data)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "LASTPASS_CID": '1234',
    }

    cartography.intel.lastpass.users.load_users(
        neo4j_session,
        formatted_data,
        common_job_parameters,
    )

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:LastpassUser) RETURN e.id, e.email;
        """,
    )
    expected_nodes = {
        (123456, 'john.doe@domain.tld'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.email'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

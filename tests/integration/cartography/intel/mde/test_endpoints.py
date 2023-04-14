import cartography.intel.mde.endpoints
import tests.data.mde.endpoints


TEST_UPDATE_TAG = 123456789


def test_load_host_data(neo4j_session, *args):
    data = tests.data.mde.endpoints.GET_HOSTS
    cartography.intel.mde.endpoints.load_host_data(neo4j_session, data, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            "00000000000000000000000000000000"
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:MdeHost)
        RETURN n.id
        """,
    )
    actual_nodes = {
        (
            n['n.id']
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

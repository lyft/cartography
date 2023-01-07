import cartography.intel.mde.endpoints
import tests.data.rapid7.rapid7_endpoints


TEST_UPDATE_TAG = 123456789


def test_load_host_data(neo4j_session, *args):
    data = tests.data.rapid7.rapid7_endpoints.GET_HOSTS
    cartography.intel.rapid7.endpoints.load_host_data(neo4j_session, data, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            282
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:Rapid7Host)
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

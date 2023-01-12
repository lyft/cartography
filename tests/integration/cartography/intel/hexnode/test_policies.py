import cartography.intel.hexnode.device_groups
import cartography.intel.hexnode.policies
import tests.data.hexnode.device_groups
import tests.data.hexnode.policies

TEST_UPDATE_TAG = 123456789


def test_load_hexnode_policies(neo4j_session):

    data = tests.data.hexnode.policies.HEXNODE_POLICIES
    formated_data = cartography.intel.hexnode.policies.transform(data)
    cartography.intel.hexnode.policies.load(
        neo4j_session,
        formated_data,
        TEST_UPDATE_TAG,
    )

    data = tests.data.hexnode.device_groups.HEXNODE_DEVICE_GROUPS.copy()
    g, ms, p = cartography.intel.hexnode.device_groups.transform(data)
    cartography.intel.hexnode.device_groups.load(
        neo4j_session,
        g,
        ms,
        p,
        TEST_UPDATE_TAG,
    )

    # Ensure policies got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:HexnodePolicy) RETURN e.id, e.name;
        """,
    )
    expected_nodes = {
        (1, 'Sample Single app kiosk - Fire OS'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure link policy - device group
    nodes = neo4j_session.run(
        """
        MATCH(g:HexnodeDeviceGroup)-[:APPLIES_POLICY]->(p:HexnodePolicy)
        RETURN g.id, p.id
        """,
    )
    actual_nodes = {
        (
            n['g.id'],
            n['p.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            1,
            1,
        ),
    }
    assert actual_nodes == expected_nodes

import cartography.intel.hexnode.device_groups
import cartography.intel.hexnode.devices
import cartography.intel.hexnode.users
import tests.data.hexnode.device_groups
import tests.data.hexnode.devices
import tests.data.hexnode.users

TEST_UPDATE_TAG = 123456789


def test_load_hexnode_devices(neo4j_session):

    cartography.intel.hexnode.users.load(
        neo4j_session,
        tests.data.hexnode.users.HEXNODE_USERS,
        TEST_UPDATE_TAG,
    )

    data = tests.data.hexnode.devices.HEXNODE_ALL_DEVICES
    formated_data = cartography.intel.hexnode.devices.transform(data)
    cartography.intel.hexnode.devices.load(
        neo4j_session,
        formated_data,
        TEST_UPDATE_TAG,
    )

    # Ensure devices got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:HexnodeDevice) RETURN e.id, e.os_name;
        """,
    )
    expected_nodes = {
        (18, 'macOS'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.os_name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure device - user link
    nodes = neo4j_session.run(
        """
        MATCH(u:HexnodeUser)-[:OWNS_DEVICE]->(d:HexnodeDevice)
        RETURN u.id, d.id
        """,
    )
    actual_nodes = {
        (
            n['u.id'],
            n['d.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            2,
            18,
        ),
    }
    assert actual_nodes == expected_nodes


def test_load_hexnode_devicegroup(neo4j_session):

    data = tests.data.hexnode.devices.HEXNODE_ALL_DEVICES
    formated_data = cartography.intel.hexnode.devices.transform(data)
    cartography.intel.hexnode.devices.load(
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

    # Ensure groups got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:HexnodeDeviceGroup) RETURN e.id, e.name;
        """,
    )
    expected_nodes = {
        (1, 'Cartography Test'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.name'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Ensure link device - device group
    nodes = neo4j_session.run(
        """
        MATCH(d:HexnodeDevice)-[:MEMBER_OF]->(g:HexnodeDeviceGroup)
        RETURN d.id, g.id
        """,
    )
    actual_nodes = {
        (
            n['d.id'],
            n['g.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            18,
            1,
        ),
    }
    assert actual_nodes == expected_nodes

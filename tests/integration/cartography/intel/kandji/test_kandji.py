import cartography.intel.kandji
import tests.data.kandji.devices

TEST_UPDATE_TAG = 123456789


def test_load_kandji_devices_data(neo4j_session):
    _ensure_local_neo4j_has_test_kandjidevice_data(neo4j_session)

    # Test that the node was created
    expected_nodes = {
        'fc60decb-30cb-4db1-b3ec-2fa8ea1b83ed',
        'f27bcd08-f653-4930-83b0-51970e923b98',
    }
    nodes = neo4j_session.run(
        """
        MATCH (d:KandjiDevice) RETURN d.device_id;
        """,
    )
    actual_nodes = {n['d.device_id'] for n in nodes}
    assert actual_nodes == expected_nodes


def _ensure_local_neo4j_has_test_kandjidevice_data(neo4j_session):
    """Pre-load the Neo4j instance with test data"""
    devices = tests.data.kandji.devices.DEVICES['devices']
    cartography.intel.kandji.devices._load_devices(devices, neo4j_session, TEST_UPDATE_TAG)

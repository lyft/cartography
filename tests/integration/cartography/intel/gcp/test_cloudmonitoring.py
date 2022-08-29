import cartography.intel.gcp.cloudmonitoring
import tests.data.gcp.cloudmonitoring

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_monitoring_alertpolicies(neo4j_session):
    data = tests.data.gcp.cloudmonitoring.TEST_POLICIES
    cartography.intel.gcp.cloudmonitoring.load_monitoring_alertpolicies(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/policies/policy123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPMonitoringAlertPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_monitoring_metric_descriptors(neo4j_session):
    data = tests.data.gcp.cloudmonitoring.TEST_METRICS
    cartography.intel.gcp.cloudmonitoring.load_monitoring_metric_descriptors(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/metricDescriptors/metric123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPMonitoringMetricDescriptor) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_monitoring_notification_channels(neo4j_session):
    data = tests.data.gcp.cloudmonitoring.TEST_CHANELS
    cartography.intel.gcp.cloudmonitoring.load_monitoring_notification_channels(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/notificationChannels/notificationChannels123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPMonitoringNotificationChannel) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_monitoring_uptimecheckconfigs(neo4j_session):
    data = tests.data.gcp.cloudmonitoring.TEST_CONGIGS
    cartography.intel.gcp.cloudmonitoring.load_monitoring_uptimecheckconfigs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/uptimeCheckConfigs/uptimeCheckConfigs123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPMonitoringUptimeCheckConfig) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

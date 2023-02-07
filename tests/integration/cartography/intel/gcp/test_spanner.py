import cartography.intel.gcp.spanner
import tests.data.gcp.spanner
import neo4j

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_spanner_instances(neo4j_session: neo4j.Session):
    data = tests.data.gcp.spanner.TEST_INSTANCES
    cartography.intel.gcp.spanner.load_spanner_instances(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    expected_nodes = {
        'projects/project-123/instances/instance1',
        'projects/project-123/instances/instance2',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSpannerInstance) return r.name
        """,
    )

    actual_nodes = {n['r.name'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_spanner_instance_configs(neo4j_session: neo4j.Session):
    data = tests.data.gcp.spanner.TEST_INSTANCE_CONFIG
    cartography.intel.gcp.spanner.load_spanner_instance_configs(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    expected_nodes = {
        'projects/project-123/instanceConfigs/config1',
        'projects/project-123/instanceConfigs/config2',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSpannerInstanceConfig) return r.name
        """,
    )

    actual_nodes = {n['r.name'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_spanner_instance_configs_replica(neo4j_session: neo4j.Session):
    data = tests.data.gcp.spanner.TEST_INSTANCE_CONFIG_REPLICA
    cartography.intel.gcp.spanner.load_spanner_instance_configs_replicas(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    expected_nodes = {'us-central1', 'us-central2'}

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSpannerInstanceConfigReplica) return r.location
        """,
    )

    actual_nodes = {n['r.location'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_spanner_instance_database(neo4j_session: neo4j.Session):
    data = tests.data.gcp.spanner.TEST_INSTANCE_DATABASE
    cartography.intel.gcp.spanner.load_spanner_instances_databases(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    expected_nodes = {
        'projects/project-123/instances/instance1/databases/database1',
        'projects/project-123/instances/instance1/databases/database2'
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSpannerInstanceDatabase) return r.name
        """,
    )

    actual_nodes = {n['r.name'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_spanner_instance_backup(neo4j_session: neo4j.Session):
    data = tests.data.gcp.spanner.TEST_INSTANCE_BACKUP
    cartography.intel.gcp.spanner.load_spanner_instances_backups(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    expected_nodes = {
        'projects/project-123/instances/instance1/backups/backup1',
        'projects/project-123/instances/instance1/backups/backup2'
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSpannerInstanceBackup) return r.name
        """,
    )

    actual_nodes = {n['r.name'] for n in nodes}

    assert actual_nodes == expected_nodes

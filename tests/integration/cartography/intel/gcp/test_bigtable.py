import cartography.intel.gcp.bigtable
import tests.data.gcp.bigtable

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_bigtable_instances(neo4j_session):
    data = tests.data.gcp.bigtable.BIGTABLE_INSTANCE
    cartography.intel.gcp.bigtable.load_bigtable_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'instance123',
        'instance456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigtableInstance) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_bigtable_cluster(neo4j_session):
    data = tests.data.gcp.bigtable.BIGTABLE_CLUSTER
    cartography.intel.gcp.bigtable.load_bigtable_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'cluster123',
        'cluster456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigtableCluster) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_bigtable_cluster_backup(neo4j_session):
    data = tests.data.gcp.bigtable.BIGTABLE_CLUSTER_BACKUP
    cartography.intel.gcp.bigtable.load_bigtable_cluster_backups(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'clusterbackup123',
        'clusterbackup456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigtableClusterBackup) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_bigtable_cluster_table(neo4j_session):
    data = tests.data.gcp.bigtable.BIGTABLE_TABLE
    cartography.intel.gcp.bigtable.load_bigtable_tables(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'table123',
        'table456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigtableTable) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_bigtable_instance_relationship(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Bigtable Instance
    data = tests.data.gcp.bigtable.BIGTABLE_INSTANCE
    cartography.intel.gcp.bigtable.load_bigtable_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, 'instance123'),
        (TEST_PROJECT_NUMBER, 'instance456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPBigtableInstance) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_bigtable_cluster_relationship(neo4j_session):
    # Load Bigtable Instance
    data = tests.data.gcp.bigtable.BIGTABLE_INSTANCE
    cartography.intel.gcp.bigtable.load_bigtable_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Bigtable Cluster
    data = tests.data.gcp.bigtable.BIGTABLE_CLUSTER
    cartography.intel.gcp.bigtable.load_bigtable_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('instance123', 'cluster123'),
        ('instance456', 'cluster456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPBigtableInstance)-[:HAS_CLUSTER]->(n2:GCPBigtableCluster) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_bigtable_cluster_backup_relationship(neo4j_session):
    # Load Bigtable Cluster
    data = tests.data.gcp.bigtable.BIGTABLE_CLUSTER
    cartography.intel.gcp.bigtable.load_bigtable_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Bigtable Cluster Backups
    data = tests.data.gcp.bigtable.BIGTABLE_CLUSTER_BACKUP
    cartography.intel.gcp.bigtable.load_bigtable_cluster_backups(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('cluster123', 'clusterbackup123'),
        ('cluster456', 'clusterbackup456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPBigtableCluster)-[:HAS_BACKUP]->(n2:GCPBigtableClusterBackup) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_bigtable_table_relationship(neo4j_session):
    # Load Bigtable Instance
    data = tests.data.gcp.bigtable.BIGTABLE_INSTANCE
    cartography.intel.gcp.bigtable.load_bigtable_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Bigtable Table
    data = tests.data.gcp.bigtable.BIGTABLE_TABLE
    cartography.intel.gcp.bigtable.load_bigtable_tables(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('instance123', 'table123'),
        ('instance456', 'table456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPBigtableInstance)-[:HAS_TABLE]->(n2:GCPBigtableTable) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

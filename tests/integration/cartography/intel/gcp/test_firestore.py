import cartography.intel.gcp.firestore
import tests.data.gcp.firestore

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789
COLLECTION_ID = 11111111111


def test_load_firestore_databases(neo4j_session):
    data = tests.data.gcp.firestore.FIRESTORE_DATABASES
    cartography.intel.gcp.firestore.load_firestore_databases(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'firestoredatabase123',
        'firestoredatabase456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPFirestoreDatabase) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_firestore_indexes(neo4j_session):
    data = tests.data.gcp.firestore.FIRESTORE_INDEXES
    cartography.intel.gcp.firestore.load_firestore_indexes(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'index123',
        'index456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPFirestoreIndex) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_firestore_database_relationship(neo4j_session):
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

    # Load Firestore Databases
    data = tests.data.gcp.firestore.FIRESTORE_DATABASES
    cartography.intel.gcp.firestore.load_firestore_databases(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, 'firestoredatabase123'),
        (TEST_PROJECT_NUMBER, 'firestoredatabase456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPFirestoreDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_firestore_indexes_relationship(neo4j_session):
    # Load Firestore databases
    data = tests.data.gcp.firestore.FIRESTORE_DATABASES
    cartography.intel.gcp.firestore.load_firestore_databases(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Firestore Indexes
    data = tests.data.gcp.firestore.FIRESTORE_INDEXES
    cartography.intel.gcp.firestore.load_firestore_indexes(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('firestoredatabase123', 'index123'),
        ('firestoredatabase456', 'index456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPFirestoreDatabase)-[:HAS_INDEX]->(n2:GCPFirestoreIndex) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

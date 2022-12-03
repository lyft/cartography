import cartography.intel.gcp.sql
import tests.data.gcp.sql

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_sql_instances(neo4j_session):
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "instance123",
        "instance456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSQLInstance) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_sql_users(neo4j_session):
    data = tests.data.gcp.sql.CLOUD_SQL_USERS
    cartography.intel.gcp.sql.load_sql_users(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "user123",
        "user456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSQLUser) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_sql_instance_relationships(neo4j_session):
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

    # Load SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "instance123"),
        (TEST_PROJECT_NUMBER, "instance456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPSQLInstance) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_sql_user_relationship(neo4j_session):
    # Load test SQL Instances
    data = tests.data.gcp.sql.CLOUD_SQL_INSTANCES
    cartography.intel.gcp.sql.load_sql_instances(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load test SQL Users
    data = tests.data.gcp.sql.CLOUD_SQL_USERS
    cartography.intel.gcp.sql.load_sql_users(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('instance123', 'user123'),
        ('instance456', 'user456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPSQLInstance)-[:USED_BY]->(n2:GCPSQLUser) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

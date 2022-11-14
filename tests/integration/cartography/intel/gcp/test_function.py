import cartography.intel.gcp.cloudfunction
import tests.data.gcp.function

TEST_PROJECT_NUMBER = 'abcd12345'
TEST_UPDATE_TAG = 123456789
TEST_REGION = 'us-east-1a'


def test_load_cloud_functions(neo4j_session):
    data = tests.data.gcp.function.CLOUD_FUNCTION
    cartography.intel.gcp.cloudfunction.load_functions(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "function123",
        "function456",
    }

    nodes = neo4j_session.run(
        """
            MATCH (f:GCPFunction) RETURN f.id;
        """,
    )

    actual_nodes = {n['f.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_function_relationships(neo4j_session):
    # CREATE TEST GCP PROJECT
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # LOAD GCP FUNCTIONS
    data = tests.data.gcp.function.CLOUD_FUNCTION
    cartography.intel.gcp.cloudfunction.load_functions(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "function123"),
        (TEST_PROJECT_NUMBER, "function456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPFunction) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

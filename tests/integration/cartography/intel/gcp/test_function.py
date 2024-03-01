import cartography.intel.gcp.cloudfunction
import tests.data.gcp.function
from cartography.util import run_analysis_job

TEST_PROJECT_NUMBER = 'abcd12345'
TEST_UPDATE_TAG = 123456789
TEST_REGION = 'us-east-1a'
TEST_FUNCTION_ID = 'function123'

TEST_WORKSPACE_ID = '1223344'
TEST_UPDATE_TAG = 123456789

common_job_parameters = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "WORKSPACE_ID": '1223344',
    "GCP_PROJECT_ID": TEST_PROJECT_NUMBER,
}


def cloudanix_workspace_to_gcp_project(neo4j_session):
    query = """
    MERGE (w:CloudanixWorkspace{id: $WorkspaceId})
    MERGE (project:GCPProject{id: $ProjectId})
    MERGE (w)-[:OWNER]->(project)
    """
    nodes = neo4j_session.run(
        query,
        WorkspaceId=TEST_WORKSPACE_ID,
        ProjectId=TEST_PROJECT_NUMBER,
    )


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


def test_cloud_function(neo4j_session):
    cloudanix_workspace_to_gcp_project(neo4j_session)
    data = tests.data.gcp.function.CLOUD_FUNCTION
    cartography.intel.gcp.cloudfunction.load_functions(neo4j_session, data, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    bindings_data = tests.data.gcp.function.FUNCTION_POLICY_BINDINGS

    cartography.intel.gcp.cloudfunction.attach_function_to_binding(neo4j_session, TEST_FUNCTION_ID, bindings_data, TEST_UPDATE_TAG)

    query1 = """
    MATCH (function:GCPFunction)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID}) \nWHERE function.exposed_internet=true
    RETURN function.id,function.exposed_internet,function.exposed_internet_type
    """
    run_analysis_job('gcp_cloud_function_analysis.json', neo4j_session, common_job_parameters)

    objects1 = neo4j_session.run(query1, GCP_PROJECT_ID=TEST_PROJECT_NUMBER, WORKSPACE_ID=TEST_WORKSPACE_ID)

    actual_nodes = {
        (
            o['function.id'],
            o['function.exposed_internet'],
            ",".join(o['function.exposed_internet_type']),

        ) for o in objects1

    }

    expected_nodes = {

        (
            'function123',
            True,
            'allUsers,allAuthenticatedUsers',
        ),

    }

    assert actual_nodes == expected_nodes

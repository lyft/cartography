import cartography.intel.gcp.bigquery
import tests.data.gcp.bigquery
from cartography.util import run_analysis_job
TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789
TEST_REGION = 'us-east-1a'
TEST_DATASET_ID = 'dataset1'

TEST_WORKSPACE_ID = '1223344'


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


def test_load_bigquey_dataset(neo4j_session):
    data = tests.data.gcp.bigquery.TEST_DATASET
    cartography.intel.gcp.bigquery.load_bigquery_datasets(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "dataset1",
        "dataset2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigqueryDataset) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_bigquery_tables(neo4j_session):
    data = tests.data.gcp.bigquery.TEST_TABLE
    cartography.intel.gcp.bigquery.load_bigquery_tables(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "table1",
        "table2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBigqueryTable) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_bigquery_dataset_relationship(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load GCP Bigquery Dataset
    data = tests.data.gcp.bigquery.TEST_DATASET
    cartography.intel.gcp.bigquery.load_bigquery_datasets(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, 'dataset1'),
        (TEST_PROJECT_NUMBER, 'dataset2'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPBigqueryDataset) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_bigquey_dataset_table_relationship(neo4j_session):
    # Load Big Query Dataset
    data = tests.data.gcp.bigquery.TEST_DATASET
    cartography.intel.gcp.bigquery.load_bigquery_datasets(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Bigquery Table
    data = tests.data.gcp.bigquery.TEST_TABLE
    cartography.intel.gcp.bigquery.load_bigquery_tables(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('dataset1', 'table1'),
        ('dataset2', 'table2'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPBigqueryDataset)-[:HAS_TABLE]->(n2:GCPBigqueryTable) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_cloud_function(neo4j_session):
    cloudanix_workspace_to_gcp_project(neo4j_session)
    data = tests.data.gcp.bigquery.TEST_DATASET
    cartography.intel.gcp.bigquery.load_bigquery_datasets(neo4j_session, data, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    accesses_data = tests.data.gcp.bigquery.TEST_ACCESSES

    cartography.intel.gcp.bigquery.attach_dataset_to_accesses(neo4j_session, TEST_DATASET_ID, accesses_data, TEST_UPDATE_TAG)

    query1 = """
    MATCH (access:GCPAcl)-[a:APPLIES_TO]->(dataset:GCPBigqueryDataset)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})<-[:OWNER]-(:GCPOrganization{id:$GCP_ORGANIZATION_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID}) \nWHERE dataset.exposed_internet=true
    RETURN dataset.id,dataset.exposed_internet,dataset.exposed_internet_type
    """
    run_analysis_job('gcp_bigquery_dataset_analysis.json', neo4j_session, common_job_parameters)

    objects1 = neo4j_session.run(query1, GCP_PROJECT_ID=TEST_PROJECT_NUMBER, WORKSPACE_ID=TEST_WORKSPACE_ID)

    actual_nodes = {
        (
            o['dataset.id'],
            o['dataset.exposed_internet'],
            ",".join(o['dataset.exposed_internet_type']),

        ) for o in objects1

    }

    expected_nodes = {

        (
            'dataset1',
            True,
            'allAuthenticatedUsers',
        ),

    }

    assert actual_nodes == expected_nodes

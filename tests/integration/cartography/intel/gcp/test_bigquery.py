import cartography.intel.gcp.bigquery
import tests.data.gcp.bigquery


TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


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
        MERGE (gcp:GCPProject{id: {PROJECT_NUMBER}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
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

import cartography.intel.gcp.dataproc
import tests.data.gcp.dataproc

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_dataproc_clusters(neo4j_session):
    data = tests.data.gcp.dataproc.TEST_CLUSTERS
    cartography.intel.gcp.dataproc.load_dataproc_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/clusters/cluster123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDataprocCluster) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes
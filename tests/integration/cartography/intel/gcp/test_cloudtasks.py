import cartography.intel.gcp.cloudtasks
import tests.data.gcp.cloudtasks

TEST_PROJECT_ID = 'project-123'
TEST_UPDATE_TAG = 123456789


def test_cloudtasks_queue(neo4j_session):
    data = tests.data.gcp.cloudtasks.CLOUDTASKS_QUEUES
    cartography.intel.gcp.cloudtasks.load_cloudtasks_queues(neo4j_session, data, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    expected_nodes = {
        "projects/project-123/locations/us-central1/queues/queue1",
        "projects/project-123/locations/us-central1/queues/queue2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudTasksQueue) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}
    assert actual_nodes == expected_nodes

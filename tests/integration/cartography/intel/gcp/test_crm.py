import cartography.intel.gcp.crm
import tests.data.gcp.crm


TEST_UPDATE_TAG = 123456789


def test_load_gcp_projects(neo4j_session):
    data = tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES

    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("sample-id-232323", "sample-number-121212"),
    }

    nodes = neo4j_session.run(
        """
        MATCH (d:GCPProject) return d.id, d.projectnumber
        """
    )
    actual_nodes = {(n['d.id'], n['d.projectnumber']) for n in nodes}
    assert actual_nodes == expected_nodes

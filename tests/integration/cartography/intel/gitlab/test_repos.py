import cartography.intel.gitlab.repositories
import tests.data.gitlab.group

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_group(neo4j_session):
    # load repo
    cartography.intel.gitlab.repositories.load_repositories_data(
        neo4j_session,
        tests.data.gitlab.group.REPOSITORIES,
        common_job_parameters,
    )
    nodes = neo4j_session.run(
        """
        MATCH (g:GitlabRepository) RETURN g.id;
        """,
    )
    expected_nodes = {'id1', 'id2'}
    actual_nodes = {
        (
            n['g.id']
        ) for n in nodes
    }

    assert actual_nodes == expected_nodes

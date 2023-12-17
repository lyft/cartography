import cartography.intel.bitbucket.workspace
import tests.data.bitbucket.workspace

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_workspace(neo4j_session):
    cartography.intel.bitbucket.workspace.load_workspace_data(
        neo4j_session,
        tests.data.bitbucket.workspace.WORKSPACES,
        common_job_parameters,
    )

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (g:BitbucketWorkspace) RETURN g.name;
        """,
    )
    expected_nodes = {'Workspace12', 'Workspace'}
    actual_nodes = {
        (
            n['g.name']
        ) for n in nodes
    }
    
    assert actual_nodes == expected_nodes
    
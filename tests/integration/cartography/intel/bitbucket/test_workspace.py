import cartography.intel.bitbucket.workspace
import tests.data.bitbucket.workspace

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445"}

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
    # project load
    cartography.intel.bitbucket.workspace.load_projects_data(
        neo4j_session,
        tests.data.bitbucket.workspace.PROJECTS,
        common_job_parameters,
    )
    nodes = neo4j_session.run(
        """
        MATCH (g:BitbucketProjects) RETURN g.name;
        """,
    )
    expected_nodes = {'bitbuket-test', 'firstproject'}
    actual_nodes = {
        (
            n['g.name']
        ) for n in nodes
    }
    
    assert actual_nodes == expected_nodes
    
    # load repo
    cartography.intel.bitbucket.workspace.load_repositeris_data(
        neo4j_session,
        tests.data.bitbucket.workspace.REPOSITORIES,
        common_job_parameters,
    )
    nodes = neo4j_session.run(
        """
        MATCH (g:BitbucketRepository) RETURN g.uuid;
        """,
    )
    expected_nodes = {'repo1', 'repo2'}
    actual_nodes = {
        (
            n['g.uuid']
        ) for n in nodes
    }
    
    assert actual_nodes == expected_nodes
    
    
    cartography.intel.bitbucket.workspace.load_memebers_data(
        neo4j_session,
        tests.data.bitbucket.workspace.members,
        common_job_parameters,
    )
    nodes = neo4j_session.run(
        """
        MATCH (g:BitbucketMember) RETURN g.name;
        """,
    )
    expected_nodes = {'user-123', 'ABC'}
    actual_nodes = {
        (
            n['g.name']
        ) for n in nodes
    }
    
    assert actual_nodes == expected_nodes

   
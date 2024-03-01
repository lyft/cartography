import cartography.intel.bitbucket.projects
import tests.data.bitbucket.workspace

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_projects(neo4j_session):

    cartography.intel.bitbucket.projects.load_projects_data(
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

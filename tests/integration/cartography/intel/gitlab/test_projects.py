import cartography.intel.gitlab.projects
import tests.data.gitlab.group

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_projects(neo4j_session):

    cartography.intel.gitlab.projects.load_projects_data(
        neo4j_session,
        tests.data.gitlab.group.PROJECTS,
        common_job_parameters,
    )
    nodes = neo4j_session.run(
        """
        MATCH (g:GitlabProject) RETURN g.name;
        """,
    )
    expected_nodes = {'gitlab-test', 'gitlab-test2'}
    actual_nodes = {
        (
            n['g.name']
        ) for n in nodes
    }

    assert actual_nodes == expected_nodes

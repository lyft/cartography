import cartography.intel.gitlab.dependencies
import tests.data.gitlab.group

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_workspace(neo4j_session):
    cartography.intel.gitlab.dependencies.load_dependencies_data(
        neo4j_session,
        tests.data.gitlab.group.DEPENDENCIES,
        common_job_parameters,
    )

    # Ensure users got loaded
    nodes = neo4j_session.run(
        """
        MATCH (g:GitLabDependency) RETURN g.name;
        """,
    )
    expected_nodes = {'name', 'name2'}
    actual_nodes = {
        (
            n['g.name']
        ) for n in nodes
    }

    assert actual_nodes == expected_nodes

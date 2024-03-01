import cartography.intel.bitbucket.repositories
import tests.data.bitbucket.workspace

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_workspace(neo4j_session):
    # load repo
    cartography.intel.bitbucket.repositories.load_repositeris_data(
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

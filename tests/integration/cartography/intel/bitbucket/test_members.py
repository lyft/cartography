import cartography.intel.bitbucket.members
import tests.data.bitbucket.workspace

TEST_UPDATE_TAG = 123456789
common_job_parameters={'UPDATE_TAG':'123456789',"WORKSPACE_ID":"123445","WORKSPACE_UUID":"234"}

def test_load_member(neo4j_session):
    cartography.intel.bitbucket.members.load_members_data(
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

from cartography.intel.okta import cleanup_okta_groups


TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 'ORG_ID'

COMMON_JOB_PARAMETERS = {'UPDATE_TAG': TEST_UPDATE_TAG, 'OKTA_ORG_ID': TEST_ORG_ID}


def test_cleanup_okta_groups(neo4j_session):
    # Arrange
    neo4j_session.run(
        'MERGE (:OktaOrganization{id: {ORG_ID}})-[:RESOURCE]->(:OktaGroup{id: "Group ID", lastupdated: 0000})',
        ORG_ID=TEST_ORG_ID,
    )

    # Assert 1: a group exists
    expected_nodes = {('Group ID')}
    nodes = neo4j_session.run("MATCH (g:OktaGroup) RETURN g.id")
    actual_nodes = {(n['g.id']) for n in nodes}
    assert actual_nodes == expected_nodes

    # Act
    cleanup_okta_groups(neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert 2: the group was cleaned up
    expected_nodes = set()
    nodes = neo4j_session.run("MATCH (g:OktaGroup) RETURN g.id")
    actual_nodes = {(n['g.id']) for n in nodes}
    assert actual_nodes == expected_nodes

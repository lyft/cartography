from unittest.mock import Mock

import cartography.intel.slack.team
import cartography.intel.slack.users
import tests.data.slack.team
import tests.data.slack.users
from tests.integration.util import check_nodes

SLACK_TEAM_ID = 'TTPQ4FBPT'
SLACK_TOKEN = 'fake-token'
TEST_UPDATE_TAG = 123456789


def test_load_slack_users(neo4j_session):
    """
    Ensure that users actually get loaded
    """

    slack_client = Mock(
        team_info=Mock(return_value=tests.data.slack.team.SLACK_TEAM),
        users_list=Mock(return_value=tests.data.slack.users.SLACK_USERS),
    )

    # Arrange
    # Slack intel only link users to existing Humans (created by other module like Gsuite)
    # We have to create mock humans to tests rels are well created by Slack module
    query = """
    UNWIND $UserData as user

    MERGE (h:Human{id: user})
    ON CREATE SET h.firstseen = timestamp()
    SET h.email = user,
    h.email = user,
    h.lastupdated = $UpdateTag
    """
    data = []
    for v in tests.data.slack.users.SLACK_USERS['members']:
        data.append(v['profile']['email'])
    neo4j_session.run(
        query,
        UserData=data,
        UpdateTag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.slack.team.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID},
    )
    cartography.intel.slack.users.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID},
    )

    # Assert Human exists
    expected_nodes = {
        ('john.doe@lyft.com', 'john.doe@lyft.com'),
        ('jane.smith@lyft.com', 'jane.smith@lyft.com'),
    }
    assert check_nodes(neo4j_session, 'Human', ['id', 'email']) == expected_nodes

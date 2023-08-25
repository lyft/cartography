from unittest.mock import Mock

import cartography.intel.slack.team
import tests.data.slack.team
from tests.integration.util import check_nodes

SLACK_TEAM_ID = 'TTPQ4FBPT'
SLACK_TOKEN = 'fake-token'
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID, 'CHANNELS_MEMBERSHIPS': True}


def test_load_slack_team(neo4j_session):
    """
    Ensure that users actually get loaded
    """

    slack_client = Mock(
        team_info=Mock(return_value=tests.data.slack.team.SLACK_TEAM),
    )

    # Act
    cartography.intel.slack.team.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert Team exists
    expected_nodes = {
        (SLACK_TEAM_ID, 'Lyft OSS'),
    }
    assert check_nodes(neo4j_session, 'SlackTeam', ['id', 'name']) == expected_nodes

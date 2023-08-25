from unittest.mock import Mock

import cartography.intel.slack.channels
import cartography.intel.slack.team
import cartography.intel.slack.users
import tests.data.slack.channels
import tests.data.slack.team
import tests.data.slack.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

SLACK_TEAM_ID = 'TTPQ4FBPT'
SLACK_TOKEN = 'fake-token'
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID, 'CHANNELS_MEMBERSHIPS': True}


def test_load_slack_channels(neo4j_session):
    """
    Ensure that channels actually get loaded
    """

    slack_client = Mock(
        team_info=Mock(return_value=tests.data.slack.team.SLACK_TEAM),
        users_list=Mock(return_value=tests.data.slack.users.SLACK_USERS),
        conversations_list=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS),
        conversations_members=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS_MEMBERSHIPS),
    )

    # Act
    cartography.intel.slack.team.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    cartography.intel.slack.users.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    cartography.intel.slack.channels.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert Channels exists
    expected_nodes = {
        ('SLACKCHANNEL2', 'random'),
        ('SLACKCHANNEL1', 'concern-marketing-comm'),
    }
    assert check_nodes(neo4j_session, 'SlackChannel', ['id', 'name']) == expected_nodes

    # Assert Channels are connected to team
    expected_rels = {
        ('SLACKCHANNEL2', SLACK_TEAM_ID),
        ('SLACKCHANNEL1', SLACK_TEAM_ID),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackTeam', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Assert Channels are connected to Creator
    expected_rels = {
        ('SLACKCHANNEL2', 'SLACKUSER1'),
        ('SLACKCHANNEL1', 'SLACKUSER1'),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackUser', 'id',
        'CREATED',
        rel_direction_right=False,
    ) == expected_rels

    # Assert Channels are connected to Members
    expected_rels = {
        ('SLACKCHANNEL2', 'SLACKUSER1'),
        ('SLACKCHANNEL1', 'SLACKUSER1'),
        ('SLACKCHANNEL2', 'SLACKUSER2'),
        ('SLACKCHANNEL1', 'SLACKUSER2'),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackUser', 'id',
        'MEMBER_OF',
        rel_direction_right=False,
    ) == expected_rels

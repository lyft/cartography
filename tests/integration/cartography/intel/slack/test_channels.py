from unittest.mock import Mock

import cartography.intel.slack.team
import cartography.intel.slack.users
import cartography.intel.slack.channels
import tests.data.slack.team
import tests.data.slack.users
import tests.data.slack.channels
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

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
        conversations_list=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS),
        conversations_members=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS_MEMBERSHIPS),
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
    cartography.intel.slack.channels.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID},
    )

    # Assert Channels exists
    expected_nodes = {
        ('PPPPOOOOIIII', 'random'),
        ('RRRRTTTTYYYYY', 'concern-marketing-comm'),
    }
    assert check_nodes(neo4j_session, 'SlackChannel', ['id', 'name']) == expected_nodes

    # Assert Channels are connected to team
    expected_rels = {
        ('PPPPOOOOIIII', SLACK_TEAM_ID),
        ('RRRRTTTTYYYYY', SLACK_TEAM_ID),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackTeam', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Assert Channels are connected to Creator
    expected_rels = {
        ('PPPPOOOOIIII', 'AAAABBBBCCCC'),
        ('RRRRTTTTYYYYY', 'AAAABBBBCCCC'),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackUser', 'id',
        'CREATED_BY',
        rel_direction_right=True,
    ) == expected_rels

    # Assert Channels are connected to Members
    expected_rels = {
        ('PPPPOOOOIIII', 'AAAABBBBCCCC'),
        ('RRRRTTTTYYYYY', 'AAAABBBBCCCC'),
        ('PPPPOOOOIIII', 'QQQQWWWWEEEE'),
        ('RRRRTTTTYYYYY', 'QQQQWWWWEEEE'),
    }
    assert check_rels(
        neo4j_session,
        'SlackChannel', 'id',
        'SlackUser', 'id',
        'MEMBER_OF',
        rel_direction_right=False,
    ) == expected_rels

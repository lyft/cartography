from unittest.mock import Mock

import cartography.intel.slack.team
import cartography.intel.slack.users
import cartography.intel.slack.channels
import cartography.intel.slack.groups
import tests.data.slack.team
import tests.data.slack.users
import tests.data.slack.channels
import tests.data.slack.usergroups
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

SLACK_TEAM_ID = 'TTPQ4FBPT'
SLACK_TOKEN = 'fake-token'
TEST_UPDATE_TAG = 123456789


def test_load_slack_groups(neo4j_session):
    """
    Ensure that users actually get loaded
    """

    slack_client = Mock(
        team_info=Mock(return_value=tests.data.slack.team.SLACK_TEAM),
        users_list=Mock(return_value=tests.data.slack.users.SLACK_USERS),
        conversations_list=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS),
        conversations_members=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS_MEMBERSHIPS),
        usergroups_list=Mock(return_value=tests.data.slack.usergroups.SLACK_USERGROUPS),
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
    cartography.intel.slack.groups.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TEAM_ID": SLACK_TEAM_ID},
    )

    # Assert groups exists
    expected_nodes = {
        ('SLACKGROUP1', 'Mobile Dev team'),
        ('SLACKGROUP2', 'Security Team'),
    }
    assert check_nodes(neo4j_session, 'SlackGroup', ['id', 'name']) == expected_nodes

    # Assert groups are connected to team
    expected_rels = {
        ('SLACKGROUP1', SLACK_TEAM_ID),
        ('SLACKGROUP2', SLACK_TEAM_ID),
    }
    assert check_rels(
        neo4j_session,
        'SlackGroup', 'id',
        'SlackTeam', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Assert groups are connected to Creator
    expected_rels = {
        ('SLACKGROUP1', 'SLACKUSER1'),
        ('SLACKGROUP2', 'SLACKUSER1'),
    }
    assert check_rels(
        neo4j_session,
        'SlackGroup', 'id',
        'SlackUser', 'id',
        'CREATED_BY',
        rel_direction_right=True,
    ) == expected_rels

    # Assert groups are connected to Members
    expected_rels = {
        ('SLACKGROUP1', 'SLACKUSER1'),
        ('SLACKGROUP2', 'SLACKUSER1'),
        ('SLACKGROUP1', 'SLACKUSER2'),
    }
    assert check_rels(
        neo4j_session,
        'SlackGroup', 'id',
        'SlackUser', 'id',
        'MEMBER_OF',
        rel_direction_right=False,
    ) == expected_rels

    # Assert groups are connected to channels
    expected_rels = {
        ('SLACKGROUP1', 'SLACKCHANNEL1'),
        ('SLACKGROUP2', 'SLACKCHANNEL2'),
    }
    assert check_rels(
        neo4j_session,
        'SlackGroup', 'id',
        'SlackChannel', 'id',
        'MEMBER_OF',
        rel_direction_right=True,
    ) == expected_rels

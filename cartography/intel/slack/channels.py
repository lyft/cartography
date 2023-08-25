import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.slack.channels import SlackChannelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    slack_client: WebClient,
    team_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    channels = get(slack_client, team_id, common_job_parameters['CHANNELS_MEMBERSHIPS'])
    load_channels(neo4j_session, channels, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str, get_memberships: bool, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
    channels: List[Dict[str, Any]] = []
    channels_info = slack_client.conversations_list(cursor=cursor, team_id=team_id)
    for m in channels_info['channels']:
        if m['is_archived']:
            channels.append(m)
        elif get_memberships:
            for i in _get_membership(slack_client, m['id']):
                channel_m = m.copy()
                channel_m['member_id'] = i
                channels.append(channel_m)
    next_cursor = channels_info.get('response_metadata', {}).get('next_cursor', '')
    if next_cursor != '':
        channels.extend(get(slack_client, team_id, get_memberships, cursor=next_cursor))
    return channels


def _get_membership(slack_client: WebClient, slack_channel: str, cursor: Optional[str] = None) -> List[str]:
    result = []
    memberships = slack_client.conversations_members(channel=slack_channel, cursor=cursor)
    for m in memberships['members']:
        result.append(m)
    next_cursor = memberships.get('response_metadata', {}).get('next_cursor', '')
    if next_cursor != '':
        result.extend(_get_membership(slack_client, slack_channel, cursor=next_cursor))
    return result


def load_channels(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackChannelSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(SlackChannelSchema(), common_job_parameters).run(neo4j_session)

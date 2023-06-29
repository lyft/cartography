import logging
from itertools import zip_longest
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.slack.group import SlackGroupSchema
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
    groups = get(slack_client, team_id)
    formated_groups = transform(groups)
    load_groups(neo4j_session, formated_groups, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    groups_info = slack_client.usergroups_list(
        cursor=cursor,
        include_count=True,
        include_users=True,
        include_disabled=True,
        team_id=team_id,
    )
    for g in groups_info['usergroups']:
        groups.append(g)
    next_cursor = groups_info.get('response_metadata', {}).get('next_cursor', '')
    if next_cursor != '':
        groups.extend(get(slack_client, team_id, cursor=next_cursor))
    return groups


@timeit
def transform(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    splitted_groups: List[Dict[str, Any]] = []
    for group in groups:
        if len(group['description']) == 0:
            group['description'] = None
        for ms in zip_longest(group['users'], group['prefs']['channels']):
            formated_group = group.copy()
            formated_group.pop('users')
            formated_group.pop('prefs')
            formated_group['member_id'] = ms[0]
            formated_group['channel_id'] = ms[1]
            splitted_groups.append(formated_group)
    return splitted_groups


def load_groups(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackGroupSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(SlackGroupSchema(), common_job_parameters).run(neo4j_session)

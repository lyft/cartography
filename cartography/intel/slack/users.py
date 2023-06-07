import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.slack.user import SlackUserSchema
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
    users = get(slack_client, team_id)
    load_users(neo4j_session, users, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    members_info = slack_client.users_list(cursor=cursor, team_id=team_id)
    for m in members_info['members']:
        result.append(m)
    next_cursor = members_info.get('response_metadata', {}).get('next_cursor', '')
    if next_cursor != '':
        result.extend(get(slack_client, team_id, cursor=next_cursor))
    return result


def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackUserSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(SlackUserSchema(), common_job_parameters).run(neo4j_session)

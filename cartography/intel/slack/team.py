import logging
from typing import Any
from typing import Dict

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.models.slack.team import SlackTeamSchema
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
    team = get(slack_client, team_id)
    load_team(neo4j_session, team, update_tag)


@timeit
def get(slack_client: WebClient, team_id: str) -> Dict[str, Any]:
    team_info = slack_client.team_info(team_id=team_id)
    return team_info['team']


def load_team(
    neo4j_session: neo4j.Session,
    data: Dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackTeamSchema(),
        [data],
        lastupdated=update_tag,
    )

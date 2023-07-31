import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.clevercloud.user import CleverCloudUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: OAuth1Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    users = get(session, common_job_parameters)
    load(neo4j_session, users, common_job_parameters)


@timeit
def get(session: OAuth1Session, common_job_parameters: Dict[str, Any]) -> List[dict]:
    org_id = common_job_parameters['ORG_ID']
    req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}/members", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


def load(
    neo4j_session: neo4j.Session,
    data: List[dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    query = build_ingestion_query(CleverCloudUserSchema())
    load_graph_data(
        neo4j_session,
        query,
        data,
        org_id=common_job_parameters['ORG_ID'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )

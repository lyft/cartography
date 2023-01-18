import logging
from typing import Dict
from typing import List

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.clevercloud.schema import CleverCloudUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    session: OAuth1Session,
    org_id: str
) -> None:
    users = get(session, org_id)
    load(neo4j_session, users, update_tag, org_id)


@timeit
def get(session: OAuth1Session, org_id: str) -> List[dict]:
    req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}/members", timeout=20)
    req.raise_for_status()
    return req.json()


def load(
    neo4j_session: neo4j.Session,
    data: List[dict],
    update_tag: int,
    org_id: str
) -> None:

    query = build_ingestion_query(CleverCloudUserSchema())
    load_graph_data(
        neo4j_session,
        query,
        data,
        orgId=org_id,
        lastupdated=update_tag,
    )

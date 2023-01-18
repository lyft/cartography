import logging
from typing import Dict
from typing import List

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.clevercloud.schema import CleverCloudOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    session: OAuth1Session,
    org_id: str
) -> None:
    organization = get(session, org_id)
    load(neo4j_session, organization, update_tag)


@timeit
def get(session: OAuth1Session, org_id: str) -> dict:
    req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}", timeout=20)
    req.raise_for_status()
    return req.json()


def load(
    neo4j_session: neo4j.Session,
    data: dict,
    update_tag: int,
) -> None:

    query = build_ingestion_query(CleverCloudOrganizationSchema())
    load_graph_data(
        neo4j_session,
        query,
        [data,],
        lastupdated=update_tag,
    )

import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.clevercloud.schema import CleverCloudApplicationSchema
from cartography.intel.dns import ingest_dns_record_by_fqdn
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    session: OAuth1Session,
    org_id: str
) -> None:
    data = get(session, org_id)
    apps, apps_vhosts = transform(data)
    load(neo4j_session, apps, apps_vhosts, update_tag)

@timeit
def get(session: OAuth1Session, org_id: str) -> List[dict]:
    req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}/applications", timeout=20)
    req.raise_for_status()
    return req.json()

@timeit
def transform(response_objects: List[dict]) -> Tuple[List[Dict], List[Dict]]:
    apps_vhosts = []
    apps = []

    for app in response_objects:
        apps.append(app)
        for vhost in app['vhosts']:
            apps_vhosts.append({'app_id': app['id'], 'fqdn': vhost['fqdn']})
    
    return apps, apps_vhosts

def load(
    neo4j_session: neo4j.Session,
    apps: List[Dict],
    apps_vhosts: List[Dict],
    update_tag: int
) -> None:

    query = build_ingestion_query(CleverCloudApplicationSchema())
    load_graph_data(
        neo4j_session,
        query,
        apps,
        lastupdated=update_tag,
    )

    # Link apps to VHosts
    for link in apps_vhosts:
        ingest_dns_record_by_fqdn(
            neo4j_session, update_tag, link['fqdn'], link['app_id'],
            record_label="CleverCloudApplication", dns_node_additional_label="CleverCloudDNSRecord",
        )


import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.clevercloud.schema import CleverCloudAddonSchema
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
    load(neo4j_session, data, update_tag, org_id)

@timeit
def get(session: OAuth1Session, org_id: str) -> List[dict]:
    result = []
    req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}/addons", timeout=20)
    req.raise_for_status()
    for addon in req.json():
        sub_req = session.get(f"https://api.clever-cloud.com/v2/organisations/{org_id}/addons/{addon['id']}/applications", timeout=20)
        sub_req.raise_for_status()
        addon['applications'] = []
        for app in sub_req.json():
            addon['applications'].append(app['id'])
        result.append(addon)
    return result

def load(
    neo4j_session: neo4j.Session,
    addons: List[Dict],
    update_tag: int,
    org_id: str
) -> None:

    query = build_ingestion_query(CleverCloudAddonSchema())
    load_graph_data(
        neo4j_session,
        query,
        addons,
        orgId=org_id,
        lastupdated=update_tag,
    )

    # WIP: Link addons to apps
    link_query = """
    UNWIND $Addons as addon
    UNWIND addon.applications as app
    MATCH (a:CleverCloudAddon {id: addon.id}), (b:CleverCloudApplication {id: app})
    MERGE (b)-[r:USES]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        link_query,
        Addons=addons,
        UpdateTag=update_tag,
    )

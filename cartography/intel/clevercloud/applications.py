import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from requests_oauthlib import OAuth1Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.dns import ingest_dns_record_by_fqdn
from cartography.models.clevercloud.app import CleverCloudApplicationSchema
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
    data = get(session, common_job_parameters)
    apps, apps_vhosts = transform(data)
    load(neo4j_session, apps, apps_vhosts, common_job_parameters)


@timeit
def get(session: OAuth1Session, common_job_parameters: Dict[str, Any]) -> List[dict]:
    org_id = common_job_parameters['ORG_ID']
    result = []

    req = session.get(
        f"https://api.clever-cloud.com/v2/organisations/{org_id}/applications",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    for app in req.json():
        sub_req = session.get(
            f"https://api.clever-cloud.com/v2/organisations/{org_id}/applications/{app['id']}/addons",
            timeout=_TIMEOUT,
        )
        sub_req.raise_for_status()
        app['addons'] = []
        for addon in sub_req.json():
            app['addons'].append(addon['id'])
        result.append(app)

    return result


@timeit
def transform(response_objects: List[dict]) -> Tuple[List[Dict], List[Dict]]:
    apps_vhosts = []
    apps = []

    for app in response_objects:
        # Duplicate app to handle high cardinality
        if len(app['addons']) == 0:
            apps.append(app)
        else:
            for addon in app['addons']:
                n_app = app.copy()
                n_app['addon_id'] = addon
                apps.append(n_app)
        # Vhosts
        for vhost in app['vhosts']:
            apps_vhosts.append({'app_id': app['id'], 'fqdn': vhost['fqdn']})

    return apps, apps_vhosts


def load(
    neo4j_session: neo4j.Session,
    apps: List[Dict],
    apps_vhosts: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    query = build_ingestion_query(CleverCloudApplicationSchema())
    load_graph_data(
        neo4j_session,
        query,
        apps,
        org_id=common_job_parameters['ORG_ID'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )

    # Link apps to VHosts
    for link in apps_vhosts:
        ingest_dns_record_by_fqdn(
            neo4j_session, common_job_parameters['UPDATE_TAG'], link['fqdn'], link['app_id'],
            record_label="CleverCloudApplication", dns_node_additional_label="CleverCloudDNSRecord",
        )

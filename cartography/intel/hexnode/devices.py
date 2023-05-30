import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hexnode.device import HexnodeDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: Session,
    api_url: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    devices = get(api_session, api_url)
    formated_devices = transform(devices)
    load(neo4j_session, formated_devices, common_job_parameters)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    devices = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/devices/', params=params, timeout=10)
    req.raise_for_status()

    for r in req.json()['results']:
        devices.append(r)

    if req.json().get('next') is not None:
        devices += get(api_session, api_url, page=page + 1)

    return devices


@timeit
def transform(devices: List[Dict]) -> List[Dict]:
    result = []
    for device in devices:
        n_device = device.copy()
        n_device['enrolled_time'] = int(dt_parse.parse(device['enrolled_time']).timestamp() * 1000)
        n_device['last_reported'] = int(dt_parse.parse(device['last_reported']).timestamp() * 1000)
        result.append(n_device)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    device_query = build_ingestion_query(HexnodeDeviceSchema())
    load_graph_data(
        neo4j_session,
        device_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
        tenant=common_job_parameters['TENANT'],
    )

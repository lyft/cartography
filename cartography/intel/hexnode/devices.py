import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    api_session: Session,
    api_url: str,
) -> None:
    devices = get(api_session, api_url)
    formated_devices = transform(devices)
    load(neo4j_session, formated_devices, update_tag)


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
        device['enrolled_time'] = dt_parse.parse(device['enrolled_time'])
        device['last_reported'] = dt_parse.parse(device['last_reported'])
        result.append(device)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:

    query = """
    UNWIND $DeviceData as device
    MERGE (d:HexnodeDevice{id: device.id})
    ON CREATE set d.firstseen = timestamp()
    SET d.lastupdated = $UpdateTag,
    d.id = device.id,
    d.name = device.device_name,
    d.model_name = device.model_name,
    d.os_name = device.os_name,
    d.os_version = device.os_version,
    d.enrolled_time = device.enrolled_time,
    d.last_reported = device.last_reported,
    d.compliant = device.compliant,
    d.serial_number = device.serial_number,
    d.udid = device.udid,
    d.enrollment_status = device.enrollment_status,
    d.imei = device.imei

    WITH d, device
    MATCH (u:HexnodeUser {id: device.user.id})
    MERGE (u)-[r:OWNS_DEVICE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        DeviceData=data,
        UpdateTag=update_tag,
    )

import logging
from typing import Dict
from typing import List

import neo4j

from cartography.intel.kandji.util import call_kandji_api
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def _get_devices(kandji_base_uri: str, kandji_token: str) -> List[Dict]:
    return call_kandji_api("/api/v1/devices", kandji_base_uri, kandji_token)


@timeit
def _load_devices(data: Dict, neo4j_session: neo4j.Session, update_tag: int) -> None:
    ingest_kandji_device = """
    UNWIND $JsonData as device
    MERGE (d:KandjiDevice{id: device.device_id})
    ON CREATE SET d.name = device.name, d.firstseen = timestamp()
    SET d.lastupdated = $UpdateTag,
        d.serial_number = device.serial_number,
        d.device_name = device.device_name,
        d.model = device.model,
        d.platform = device.platform,
        d.os_version = device.os_version,
        d.last_check_in = device.last_check_in
    """
    neo4j_session.run(ingest_kandji_device, JsonData=data, UpdateTag=update_tag)


@timeit
def _sync_devices(
    neo4j_session: neo4j.Session, update_tag: int, kandji_base_uri: str, kandji_token: str,
) -> bool:
    devices = _get_devices(kandji_base_uri, kandji_token)
    _load_devices(devices, neo4j_session, update_tag)  # type: ignore
    return True


@timeit
def sync(
    neo4j_session: neo4j.Session, kandji_base_uri: str, kandji_token: str,
    common_job_parameters: Dict,
) -> None:
    sync_successful = _sync_devices(
        neo4j_session, common_job_parameters['UPDATE_TAG'],
        kandji_base_uri, kandji_token,
    )
    if sync_successful:
        logger.info('Kandji device sync successful')

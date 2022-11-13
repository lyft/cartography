"""
cartography/intel/sumologic/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from .util import sumologic_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: Tuple[str, str, str],
) -> None:
    sumologic_hosts_list = sumologic_hosts(authorization)
    for host_data in sumologic_hosts_list:
        load_host_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:SumologicHost{hostname: host.hostname})
        ON CREATE SET h.hostname = host.hostname,
            h.sumologic_instance = host.instance,
            h.tool_first_seen = host.firstseen
        SET h.short_hostname = host.short_hostname,
            h.tool_last_seen = host.lastseen,
            h.sumologic_bu = host.bu,
            h.sumologic_dc = host.dc,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
    """
    logger.info("Loading %s sumologic hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

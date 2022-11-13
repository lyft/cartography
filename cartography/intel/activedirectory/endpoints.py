"""
cartography/intel/sumologic/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from .util import activedirectory_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: Tuple[str, str],
) -> None:
    activedirectory_hosts_list = activedirectory_hosts(authorization)
    for host_data in activedirectory_hosts_list:
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
        MERGE (h:ActiveDirectoryHost{hostname: host.hostname})
        ON CREATE SET h.hostname = host.hostname,
            h.ad_domain = host.ad_domain,
            h.firstseen = timestamp()
        SET h.short_hostname = host.short_hostname,
            h.objectid = host.objectid,
            h.distinguishedname = host.distinguishedname,
            h.unconstraineddelegation = host.unconstraineddelegation,
            h.enabled = host.enabled,
            h.highvalue = host.highvalue,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
    """
    logger.info("Loading %s activedirectory hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

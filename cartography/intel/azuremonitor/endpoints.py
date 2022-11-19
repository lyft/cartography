"""
cartography/intel/azuremonitor/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from .util import azuremonitor_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: Tuple[str, str],
) -> None:
    azuremonitor_hosts_list = azuremonitor_hosts(authorization)
    for host_data in azuremonitor_hosts_list:
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
        MERGE (h:AzureMonitorHost{hostname: host.Computer})
        ON CREATE SET h.hostname = host.Computer,
            h.short_hostname = toLower(host.Computer),
            h.resource_id = host.resource_id,
            h.resource_group = host.resource_group,
            h.subscription_id = host.subscription_id,
            h.tenant_id = host.TenantId,
            h.sentinel_sourcesystem = host.SourceSystem,
            h.sentinel_host_ip = host.HostIP,
            h.workspace = host.workspace,
            h.tool_first_seen = host.firstseen,
            h.platform = host.systemtype,
            h.workspace_name = host.workspace_name
        SET h.tool_last_seen = host.lastseen,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
    """
    logger.debug("Loading %s azuremonitor hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

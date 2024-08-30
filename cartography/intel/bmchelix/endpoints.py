"""
cartography/intel/bmchelix/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from .util import get_bmchelix_hosts
from .util import get_bmchelix_virtualmachines
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: Tuple[str, str, bool],
) -> None:
    bmchelix_hosts_list = get_bmchelix_hosts(authorization)
    for host_data in bmchelix_hosts_list:
        load_host_data(neo4j_session, host_data, update_tag)

    bmchelix_vm_list = get_bmchelix_virtualmachines(authorization)
    for host_data in bmchelix_vm_list:
        load_vm_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information

    FIXME!
    neo4j.exceptions.CypherTypeError: {code: Neo.ClientError.Statement.TypeError}
    {message: Collections containing null values can not be stored in properties.}
    = how to identify problematic row/column?
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:BmcHelixHost{bmchelix_uuid: host.uuid})
        ON CREATE SET h.bmchelix_uuid = host.uuid,
            h.firstseen = timestamp()
        SET h.status = host.status,
            h.hostname = host.name,
            h.short_hostname = host.short_hostname,
            h.platform_name = host.vm_os_type,
            h.os = host.vm_os,
            h.hw_vendor = host.hw_vendor,
            h.virtual = host.virtual,
            h.cloud = host.cloud,
            h.tool_first_seen = host.firstSeen,
            h.tool_last_seen = host.tool_last_seen,
            h.vm_power_state = host.vm_power_state,
            h.instance_id = host.instance_id,
            h.subscription_id = host.subscription_id,
            h.resource_group = host.resource_group,
            h.resource_id = host.vmMetadata_resourceId,
            h.tags_costcenter = host.tags_costcenter,
            h.tags_engcontact = host.tags_engcontact,
            h.tags_businesscontact = host.tags_businesscontact,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureSubscription{id: h.subscription_id})
        MERGE (s)-[r:CONTAINS]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{id: h.resource_id})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    logger.debug("Loading %s bmchelix hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )


def load_vm_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:BmcHelixVirtualMachines{bmchelix_uuid: host.uuid})
        ON CREATE SET h.bmchelix_uuid = host.uuid,
            h.firstseen = timestamp()
        SET h.status = host.status,
            h.hostname = host.hostname,
            h.short_hostname = host.short_hostname,
            h.platform_name = host.vm_os_type,
            h.os = host.vm_os,
            h.hw_vendor = host.hw_vendor,
            h.virtual = host.virtual,
            h.cloud = host.cloud,
            h.tool_first_seen = host.firstSeen,
            h.tool_last_seen = host.tool_last_seen,
            h.vm_power_state = host.vm_power_state,
            h.instance_id = host.instance_id,
            h.subscription_id = host.subscription_id,
            h.resource_group = host.resource_group,
            h.resource_id = host.resource_id,
            h.tags_costcenter = host.tags_costcenter,
            h.tags_engcontact = host.tags_engcontact,
            h.tags_businesscontact = host.tags_businesscontact,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureSubscription{id: h.subscription_id})
        MERGE (s)-[r:CONTAINS]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{id: h.resource_id})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    logger.debug("Loading %s bmchelix virtual machines.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

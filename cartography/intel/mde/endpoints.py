"""
cartography/intel/mde/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List

import neo4j

from .util import mde_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: str,
) -> None:
    mde_hosts_list = mde_hosts(authorization)
    for host_data in mde_hosts_list:
        load_host_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information

    Note: part of fields copies from crowdstrike. MDE taxonomy may be different.
      add tenant id/name field? normalized hostname?
      passing some fields as string, else error:
      'message: Property values can only be of primitive types or arrays thereof.'

    FIXME! Processing per batch of 28 hosts? mde api per 10k hosts?
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:MdeHost{id: host.id})
        ON CREATE SET h.mde_id = host.id,
            h.firstseen = timestamp()
        SET h.status = host.status,
            h.hostname = host.computerDnsName,
            h.machine_domain = host.machine_domain,
            h.tool_first_seen = host.firstSeen,
            h.tool_last_seen = host.lastSeen,
            h.platform_name = host.osPlatform,
            h.os_version = host.osVersion,
            h.cpu_signature = host.osProcessor,
            h.agent_version = host.agentVersion,
            h.local_ip = host.lastIpAddress,
            h.external_ip = host.lastExternalIpAddress,
            h.cloud_provider = host.vmMetadata_cloudProvider,
            h.instance_id = host.vmMetadata_vmId,
            h.subscription_id = host.vmMetadata_subscriptionId,
            h.resource_group = host.resource_group,
            h.resource_id = host.vmMetadata_resourceId,
            // MDE fields
            h.mde_healthstatus = host.healthStatus,
            h.mde_devicevalue = host.deviceValue,
            h.mde_riskscore = host.riskScore,
            h.mde_exposurelevel = host.exposureLevel,
            h.mde_isadjoined = host.isAadJoined,
            h.mde_aaddeviceid = host.aadDeviceId,
            h.mde_machinetags = host.machineTags,
            h.mde_defenderavstatus = host.defenderAvStatus,
            h.mde_onboardingstatus = host.onboardingStatus,
            h.mde_osarchitecture = host.osArchitecture,
            h.mde_managedby = host.managedBy,
            h.mde_managedbystatus = host.managedByStatus,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{id: h.resource_id})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    logger.info("Loading %s mde hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

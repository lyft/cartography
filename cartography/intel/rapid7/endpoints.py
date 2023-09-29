"""
cartography/intel/rapid7/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j

from .util import get_rapid7_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: Tuple[str, str, str, str, str, int],
) -> None:
    r7_hosts = get_rapid7_hosts(authorization)
    for host_data in r7_hosts:
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
        MERGE (h:Rapid7Host{id: host.id})
        ON CREATE SET h.r7_id = host.id,
            h.firstseen = timestamp()
        SET h.r7_assessedForPolicies = host.assessedForPolicies,
            h.r7_assessedForVulnerabilities = host.assessedForVulnerabilities,
            h.hostname = host.hostName,
            h.short_hostname = host.short_hostname,
            h.r7_ip = host.ip,
            h.r7_mac = host.mac,
            h.r7_os = host.os,
            h.r7_rawriskscore = host.rawRiskScore,
            h.r7_riskscore = host.riskScore,
            h.r7_architecture = host.osFingerprint_architecture,
            h.r7_os_product = host.osFingerprint_product,
            h.r7_os_version = host.osFingerprint_version,
            h.r7_vulnerabilities_critical = host.vulnerabilities_critical,
            h.r7_vulnerabilities_exploits = host.vulnerabilities_exploits,
            h.r7_vulnerabilities_malwareKits = host.vulnerabilities_malwareKits,
            h.r7_vulnerabilities_moderate = host.vulnerabilities_moderate,
            h.r7_vulnerabilities_severe = host.vulnerabilities_severe,
            h.r7_vulnerabilities_total = host.vulnerabilities_total,
            h.tool_first_seen = host.tool_first_seen,
            h.tool_last_seen = host.tool_last_seen,
            h.r7_type = host.type,
            h.r7_sites = host.sites,
            h.r7_custom_tags = toString(host.custom_tags),
            h.r7_location_tags = toString(host.location_tags),
            h.r7_owner_tags = toString(host.owner_tags),
            h.r7_criticality_tags = toString(host.criticality_tags),
            h.cloud_provider = host.cloud_provider,
            h.instance_id = host.instance_id,
            h.subscription_id = host.subscription_id,
            h.resource_id = host.resource_id,
            h.resource_group = host.resource_group,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{id: h.resource_id})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{short_hostname: h.short_hostname})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    logger.debug("Loading %s rapid7 hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

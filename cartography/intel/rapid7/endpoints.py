"""
cartography/intel/rapid7/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List

import neo4j

from .util import rapid7_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: tuple[str, str, str, bool],
) -> None:
    r7_hosts = rapid7_hosts(authorization)
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
    """
    logger.info("Loading %s rapid7 hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

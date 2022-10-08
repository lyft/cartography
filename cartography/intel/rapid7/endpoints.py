"""
cartography/intel/rapid7/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List

import neo4j

from .util import Rapid7Hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: tuple[str, str, str, bool],
) -> None:
    rapid7_hosts = Rapid7Hosts(authorization)
    for host_data in rapid7_hosts:
        load_host_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information

    NOK array/json value?
    {code: Neo.ClientError.Statement.TypeError}
    {message: Property values can only be of primitive types or arrays thereof.
    Encountered: Map{mac -> String("00:1A:AA:01:13:12"), ip -> String("10.1.12.123")}.}
            h.r7_addresses = host.addresses,
            h.r7_configurations = host.configurations,
            h.r7_databases = host.databases,
            h.r7_files = host.files,
            h.r7_history = host.history,
            h.r7_hostnames = host.hostNames,
            h.r7_ids = host.ids,
            h.r7_links = host.links,
            h.r7_osfingerprint = host.osFingerprint,
            h.r7_services = host.services,
            h.r7_software = host.software,
            h.r7_usergroups = host.userGroups,
            h.r7_users = host.users,
            h.r7_vulnerabilities = host.vulnerabilities,
    NOK array
            h.instance_id = host.configurations[0].value.instanceId,
            h.resource_id = host.configurations[0].value.resourceId,

    For instanceId, resourceId, this supposed configurations array first or only entry is the azure one.
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
            h.r7_type = host.type,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
    """
    logger.info("Loading %s rapid7 hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_dns_zones(dns: Resource, project_id: str, common_job_parameters) -> List[Resource]:
    """
    Returns a list of DNS zones within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of DNS zones
    """
    try:
        zones = []
        request = dns.managedZones().list(project=project_id)
        while request is not None:
            response = request.execute()
            if 'managedZones' in response:
                zones.extend(response.get('managedZone', []))
            request = dns.managedZones().list_next(previous_request=request, previous_response=response)

        return zones
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve DNS zones on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_managed_zones(zones: List, project_id: str) -> List[Resource]:
    list_zones = []
    for managed_zone in zones:
        managed_zone['id'] = f"projects/{project_id}/managedZones/{managed_zone['name']}"
        managed_zone['consolelink'] = gcp_console_link.get_console_link(
            resource_name='dns_zone', project_id=project_id, dns_zone_name=managed_zone['name'],
        )
        list_zones.append(managed_zone)

    return list_zones


@timeit
def get_dns_rrs(dns: Resource, zone: Dict, project_id: str) -> List[Resource]:
    """
    Returns a list of DNS Resource Record Sets within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type dns_zones: list
    :param dns_zones: List of DNS zones for the project

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of Resource Record Sets
    """
    try:
        rrs: List[Resource] = []
        request = dns.resourceRecordSets().list(project=project_id, managedZone=zone['id'])
        while request is not None:
            response = request.execute()
            if 'rrsets' in response:
                rrs.extend(response['rrsets'])
            request = dns.resourceRecordSets().list_next(previous_request=request, previous_response=response)
        return rrs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve DNS RRS on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            # raise
            return []


@timeit
def transform_rrs(rrsets: List, zone: Dict, project_id: str):
    list_rrs = []

    for resource_record_set in rrsets:
        resource_record_set['zone'] = zone['id']
        resource_record_set['consolelink'] = gcp_console_link.get_console_link(
            resource_name='dns_resource_record_set', project_id=project_id, dns_zone_name=zone['name'], dns_rrset_name=resource_record_set['name'],
        )
        resource_record_set[
            "id"
        ] = f"projects/{project_id}/resourceRecordSet/{resource_record_set.get('name', None)}"
        list_rrs.append(resource_record_set)

    return list_rrs


@timeit
def get_dns_keys(dns: Resource, zone: Dict, project_id: str) -> List[Resource]:
    """
    Returns a list of DNS Keys within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type dns_zones: list
    :param dns_zones: List of DNS zones for the project

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of Resource Record Sets
    """
    try:
        dns_keys = []
        request = dns.dnsKeys().list(project=project_id, managedZone=zone['name'])
        while request is not None:
            response = request.execute()
            if 'dnsKeys' in response:
                dns_keys.extend(response['dnsKeys'])
            request = dns.dnsKeys().list_next(previous_request=request, previous_response=response)
        return dns_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve DNS Keys on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            # raise
            return []


@timeit
def transform_dns_keys(dnsKeys: List, project_id: str, zone: Dict):
    list_keys = []

    for key in dnsKeys:
        key['zone'] = zone['id']
        key['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='dns_home')
        key['id'] = f"projects/{project_id}/managedZones/{zone['name']}/dnsKeys/{key['id']}"
        list_keys.append(key)

    return list_keys


@timeit
def get_dns_policies(dns: Resource, project_id: str, common_job_parameters) -> List[Resource]:
    """
    Returns a list of DNS policies within the given project.

    :type dns: The GCP DNS resource object
    :param dns: The DNS resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of DNS Policies
    """
    try:
        policies = []
        request = dns.policies().list(project=project_id)
        while request is not None:
            response = request.execute()
            if 'policies' in response:
                policies.extend(response['policies'])
            request = dns.policies().list_next(previous_request=request, previous_response=response)

        return policies
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve DNS policies on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_dns_policies(policies: List[Dict], project_id: str) -> List[Dict]:
    list_policies = []

    for policy in policies:
        policy['id'] = f"projects/{project_id}/policies/{policy['name']}"
        policy['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id,
            dns_policy_name=policy['name'], resource_name='dns_policy',
        )
        list_policies.append(policy)

    return list_policies


@timeit
def load_dns_zones(neo4j_session: neo4j.Session, dns_zones: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP DNS Zones into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type dns_resp: Dict
    :param dns_resp: A DNS response object from the GKE API

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """

    ingest_records = """
    UNWIND $records as record
    MERGE (zone:GCPDNSZone{id:record.id})
    ON CREATE SET
        zone.firstseen = timestamp(),
        zone.created_at = record.creationTime
    SET
        zone.name = record.name,
        zone.dns_name = record.dnsName,
        zone.region = $region,
        zone.description = record.description,
        zone.visibility = record.visibility,
        zone.kind = record.kind,
        zone.nameservers = record.nameServers,
        zone.consolelink = record.consolelink,
        zone.lastupdated = $gcp_update_tag
    WITH zone
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(zone)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=dns_zones,
        region="global",
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_rrs(neo4j_session: neo4j.Session, dns_rrs: List[Resource], project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP RRS into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type dns_rrs: list
    :param dns_rrs: A list of RRS

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """

    ingest_records = """
    UNWIND $records as record
    MERGE (rrs:GCPRecordSet{id:record.id})
    ON CREATE SET
        rrs.firstseen = timestamp()
    SET
        rrs.name = record.name,
        rrs.type = record.type,
        rrs.region = $region,
        rrs.ttl = record.ttl,
        rrs.data = record.rrdatas,
        rrs.consolelink = record.consolelink,
        rrs.lastupdated = $gcp_update_tag
    WITH rrs, record
    MATCH (zone:GCPDNSZone{id:record.zone})
    MERGE (zone)-[r:HAS_RECORD]->(rrs)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_records,
        records=dns_rrs,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_dns_polices(neo4j_session: neo4j.Session, policies: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP DNS Policies into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type policies: Dict
    :param policies: A DNS Policies response

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """
    ingest_policies = """
    UNWIND $DNSPolicies as policy
    MERGE (pol:GCPDNSPolicy{id:policy.id})
    ON CREATE SET
        pol.firstseen = timestamp()
    SET
        pol.uniqueId = policy.id,
        pol.name = policy.name,
        pol.region = $region,
        pol.consolelink = policy.consolelink,
        pol.enableInboundForwarding = policy.enableInboundForwarding,
        pol.enableLogging = policy.enableLogging,
        pol.lastupdated = $gcp_update_tag
    WITH pol
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(pol)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_policies,
        DNSPolicies=policies,
        region="global",
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_dns_keys(neo4j_session: neo4j.Session, dns_keys: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP DNS Keys into Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type dns keys: Dict
    :param dns keys: A DNS Keys response

    :type project_id: str
    :param project_id: Current Google Project Id

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """
    ingest_keys = """
    UNWIND $DNSKeys as key
    MERGE (ky:GCPDNSKey{id:key.id})
    ON CREATE SET
        ky.firstseen = timestamp()
    SET
        ky.uniqueId = key.id,
        ky.region = $region,
        ky.algorithm = key.algorithm,
        ky.keyLength = key.keyLength,
        ky.consolelink = key.consolelink,
        ky.isActive = key.isActive,
        ky.lastupdated = $gcp_update_tag
    WITH ky, key
    MATCH (zone:GCPDNSZone{id:key.zone})
    MERGE (zone)-[r:HAS_KEY]->(ky)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        ingest_keys,
        DNSKeys=dns_keys,
        region="global",
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_dns_records(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP DNS Zones and RRS nodes and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_dns_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, dns: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:
    """
    Get GCP DNS Zones and Resource Record Sets using the DNS resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type dns: The DNS resource object created by googleapiclient.discovery.build()
    :param dns: The GCP DNS resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing DNS for project '%s', at %s.", project_id, tic)

    # DNS ZONES
    zones = get_dns_zones(dns, project_id, common_job_parameters)
    dns_zones = transform_managed_zones(zones, project_id)
    load_dns_zones(neo4j_session, dns_zones, project_id, gcp_update_tag)
    label.sync_labels(neo4j_session, dns_zones, gcp_update_tag, common_job_parameters, 'dns_zones', 'GCPDNSZone')
    # DNS POLICIES
    policies = get_dns_policies(dns, project_id, common_job_parameters)
    list_policies = transform_dns_policies(policies, project_id)
    load_dns_polices(neo4j_session, list_policies, project_id, gcp_update_tag)
    for zone in dns_zones:
        # RECORD SETS
        dns_rrs = get_dns_rrs(dns, zone, project_id)
        list_rrs = transform_rrs(dns_rrs, zone, project_id)
        load_rrs(neo4j_session, list_rrs, project_id, gcp_update_tag)
        # DNS KEYS
        dns_keys = get_dns_keys(dns, zone, project_id)
        list_keys = transform_dns_keys(dns_keys, project_id, zone)
        load_dns_keys(neo4j_session, list_keys, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_dns_records(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process DNS: {toc - tic:0.4f} seconds")



import logging
import json
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

from . import utils
#from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_vcn_list_data(
    network: oci.core.VirtualNetworkClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(network.list_vcns, compartment_id=current_tenancy_id)
    return {'VCNs': utils.oci_object_to_json(response.data)}

def load_vcn_list(
    neo4j_session: neo4j.Session,
    vcns: List[Dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_vcn = """
    MERGE (pnode:OCIVcn{id: {ID}})
    ON CREATE SET pnode.firstseen = timestamp(), pnode.createdate = {CREATE_DATE}
    SET pnode.name = {VCN_NAME}, pnode.compartmentid = {COMPARTMENT_ID},
    pnode.state = {STATE}, pnode.domainname = {DOMAIN_NAME},
    pnode.dnslabel = {DNS_LABEL},
    pnode.ipv4cidrs = {IPV4_CIDRS},  pnode.ipv6cidrs = {IPV6_CIDRS},
    pnode.byoipcidrs = {BYOIP_CIDRS}, pnode.ipv6privatecidrs = {IPV6_PRIVATE_CIDRS},
    pnode.lastupdated = {oci_update_tag}
    WITH pnode
    MATCH (aa) WHERE (aa:OCITenancy OR aa:OCICompartment) AND aa.ocid={COMPARTMENT_ID}
    MERGE (aa)-[r:OCI_VCN_IN]->(pnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {oci_update_tag}
    """

    for vcn in vcns:
        ipv4_cidrs_json = None
        ipv6_cidrs_json = None
        byoip_cidrs_json = None
        ipv6_private_cidrs_json = None
        if vcn['cidr-blocks']:
            ipv4_cidrs_json = json.dumps(vcn['cidr-blocks'])
        if vcn['ipv6-cidr-blocks']:
            ipv6_cidrs_json = json.dumps(vcn['ipv6-cidr-blocks'])
        if vcn['byoipv6-cidr-blocks']:
            byoip_cidrs_json = json.dumps(vcn['byoipv6-cidr-blocks'])
        if vcn['ipv6-private-cidr-blocks']:
            ipv6_private_cidrs_json = json.dumps(vcn['ipv6-private-cidr-blocks'])

        neo4j_session.run(
            ingest_vcn,
            ID=vcn["id"],
            VCN_NAME=vcn["display-name"],
            COMPARTMENT_ID=vcn["compartment-id"],
            STATE=vcn["lifecycle-state"],
            DOMAIN_NAME=vcn["vcn-domain-name"],
            DNS_LABEL=vcn["dns-label"],
            IPV4_CIDRS=ipv4_cidrs_json,
            IPV6_CIDRS=ipv6_cidrs_json,
            BYOIP_CIDRS=byoip_cidrs_json,
            IPV6_PRIVATE_CIDRS=ipv6_private_cidrs_json,
            CREATE_DATE=str(vcn["time-created"]),
            OCI_TENANCY_ID=current_tenancy_id,
            oci_update_tag=oci_update_tag,
        )

# Security List Fetch

def get_security_list_data(
    network: oci.core.VirtualNetworkClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(network.list_security_lists, compartment_id=current_tenancy_id)
    return {'SecurityGroups': utils.oci_object_to_json(response.data)}

def _process_security_rule(security_rule):
    temp_rule = {
        'description': security_rule['description'],
        'is_stateless': security_rule['is_stateless'],
    }
    # Get range regardless of ingress vs egress
    if 'destination' in security_rule.keys():
        temp_rule['range'] = security_rule['destination']
        temp_rule['type'] = security_rule['destination_type']
    if 'source' in security_rule.keys():
        temp_rule['range'] = security_rule['source']
        temp_rule['type'] = security_rule['source_type']

    # Handle rules differently depending on protocol
    if security_rule['icmp_options']:
        temp_rule['protocol'] = 'icmp'
        temp_rule['from_port'] = 0
        temp_rule['to_port'] = 65535
    elif security_rule['udp_options']:
        temp_rule['protocol'] = 'udp'
    elif security_rule['tcp_options']:
        temp_rule['protocol'] = 'tcp'
        if security_rule['tcp_options']['destination_port_range']:
            temp_rule['from_port'] = security_rule['tcp_options']['destination_port_range']['min']
            temp_rule['to_port'] = security_rule['tcp_options']['destination_port_range']['max']
        else:
            temp_rule['from_port'] = security_rule['tcp_options']['source_port_range']['min']
            temp_rule['to_port'] = security_rule['tcp_options']['source_port_range']['max']
    else:
        temp_rule['protocol'] = 'all'
        temp_rule['from_port'] = 0
        temp_rule['to_port'] = 65535

    return temp_rule

def _process_security_lists(secuirty_lists):
    processed_security_lists = []
    for security_list in secuirty_lists:
        temp_sg = {
            'display-name': security_list['display-name'],
            'lifecycle-state': security_list['lifecycle-state'],
            'time-created': security_list['time-created'],
            'vcn-id': security_list['vcn-id'],
            'ip_permissions_inbound': [],
            'ip_permissions_egress': []
        }
        for ip_rule in security_list['egress-security-rules']:
            temp_sg['ip_permissions_egress'].append(_process_security_rule(ip_rule))
        for ip_rule in security_list['ingress-security-rules']:
            temp_sg['ip_permissions_inbound'].append(_process_security_rule(ip_rule))
        processed_security_lists.append(temp_sg)
    return processed_security_lists

def load_security_lists(
    neo4j_session: neo4j.Session,
    security_lists: List[Dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    _ = _process_security_lists(security_lists)
    exit()

    ingest_instance = """
    MERGE (pnode:OCIInstance{id: {ID}})
    ON CREATE SET pnode.firstseen = timestamp(), pnode.createdate = {CREATE_DATE}
    SET pnode.name = {INSTANCE_NAME}, pnode.compartmentid = {COMPARTMENT_ID},
    pnode.instancetype = {INSTANCE_TYPE}, pnode.region = {REGION},
    pnode.state = {STATE}, pnode.imageid = {IMAGE_ID},
    pnode.lastupdated = {oci_update_tag}
    WITH pnode
    MATCH (aa) WHERE (aa:OCITenancy OR aa:OCICompartment) AND aa.ocid={COMPARTMENT_ID}
    MERGE (aa)-[r:OCI_INSTANCE]->(pnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {oci_update_tag}
    """

    for security_list in security_lists:
        neo4j_session.run(
            ingest_instance,
            ID=security_list["id"],
            INSTANCE_NAME=security_list["display-name"],
            COMPARTMENT_ID=security_list["compartment-id"],
            INSTANCE_TYPE=security_list["shape"],
            REGION=security_list["region"],
            STATE=security_list["lifecycle-state"],
            IMAGE_ID=security_list["image-id"],
            CREATE_DATE=str(security_list["time-created"]),
            OCI_TENANCY_ID=current_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


# list_instances
def sync_instances(
    neo4j_session: neo4j.Session,
    network: oci.core.VirtualNetworkClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
):
    logger.info("Syncing network instances for account '%s'.", current_tenancy_id)
    compartments = utils.get_compartments_in_tenancy(neo4j_session, current_tenancy_id)
    for compartment in compartments:
        logger.info(
            "Syncing OCI instances for compartment '%s' in account '%s'.", compartment['ocid'], current_tenancy_id,
        )
        data = get_vcn_list_data(network, compartment["ocid"])
        if(data["VCNs"]):
            load_vcn_list(neo4j_session, data["VCNs"], current_tenancy_id, oci_update_tag)
        # Process security lists
        data = get_security_list_data(network, compartment["ocid"])
        if(data["SecurityGroups"]):
            load_security_lists(neo4j_session, data["SecurityGroups"], current_tenancy_id, oci_update_tag)
            print(len(data["SecurityGroups"]))
        #run_cleanup_job('oci_import_instances_cleanup.json', neo4j_session, common_job_parameters)

def sync(
    neo4j_session: neo4j.Session,
    network: oci.core.VirtualNetworkClient,
    tenancy_id: str,
    region_name: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Syncing Networking for account '%s'.", tenancy_id)
    sync_instances(neo4j_session, network, tenancy_id, oci_update_tag, common_job_parameters)

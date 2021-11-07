# Google Compute Engine API-centric functions
# https://cloud.google.com/compute/docs/concepts
import json
import logging
from collections import namedtuple
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
InstanceUriPrefix = namedtuple('InstanceUriPrefix', 'zone_name project_id')


def _get_error_reason(http_error: HttpError) -> str:
    """
    Helper function to get an error reason out of the googleapiclient's HttpError object
    This function copies the structure of
    https://github.com/googleapis/google-api-python-client/blob/1d2e240a74d2bc0074dffbc57cf7d62b8146cb82/
                                  googleapiclient/http.py#L111
    At the moment this is the best way we know of to extract the HTTP failure reason.
    Additionally, see https://github.com/googleapis/google-api-python-client/issues/662.
    :param http_error: The googleapi HttpError object
    :return: The error reason as a string
    """
    try:
        data = json.loads(http_error.content.decode('utf-8'))
        if isinstance(data, dict):
            reason = data['error']['errors'][0]['reason']
        else:
            reason = data[0]['error']['errors']['reason']
    except (UnicodeDecodeError, ValueError, KeyError):
        logger.warning(f"HttpError: {data}")
        return ''
    return reason


@timeit
def get_zones_in_project(project_id: str, compute: Resource, max_results: Optional[int] = None) -> Optional[List[Dict]]:
    """
    Return the zones where the Compute Engine API is enabled for the given project_id.
    See https://cloud.google.com/compute/docs/reference/rest/v1/zones and
    https://cloud.google.com/compute/docs/reference/rest/v1/zones/list.
    If the API is not enabled or if the project returns a 404-not-found, return None.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :param max_results: Optional cap on number of results returned by this function. Default = None, which means no cap.
    :return: List of a project's zone objects if Compute API is turned on, else None.
    """
    try:
        req = compute.zones().list(project=project_id, maxResults=max_results)
        res = req.execute()
        return res['items']
    except HttpError as e:
        reason = _get_error_reason(e)
        if reason == 'accessNotConfigured':
            logger.info(
                (
                    "Google Compute Engine API access is not configured for project %s; skipping. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        elif reason == 'notFound':
            logger.info(
                (
                    "Project %s returned a 404 not found error. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        elif reason == 'forbidden':
            logger.info(
                (
                    "Your GCP identity does not have the compute.zones.list permission for project %s; skipping "
                    "compute sync for this project. Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        else:
            raise


@timeit
def get_gcp_instance_responses(project_id: str, zones: Optional[List[Dict]], compute: Resource) -> List[Resource]:
    """
    Return list of GCP instance response objects for a given project and list of zones
    :param project_id: The project ID
    :param zones: The list of zones to query for instances
    :param compute: The compute resource object
    :return: A list of response objects of the form {id: str, items: []} where each item in `items` is a GCP instance
    """
    if not zones:
        # If the Compute Engine API is not enabled for a project, there are no zones and therefore no instances.
        return []
    response_objects: List[Resource] = []
    for zone in zones:
        req = compute.instances().list(project=project_id, zone=zone['name'])
        res = req.execute()
        response_objects.append(res)
    return response_objects


@timeit
def get_gcp_subnets(projectid: str, region: str, compute: Resource) -> Resource:
    """
    Return list of all subnets in the given projectid and region
    :param projectid: THe projectid
    :param region: The region to pull subnets from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP subnets for a given project
    """
    req = compute.subnetworks().list(project=projectid, region=region)
    return req.execute()


@timeit
def get_gcp_vpcs(projectid: str, compute: Resource) -> Resource:
    """
    Get VPC data for given project
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: VPC response object
    """
    req = compute.networks().list(project=projectid)
    return req.execute()


@timeit
def get_gcp_regional_forwarding_rules(project_id: str, region: str, compute: Resource) -> Resource:
    """
    Return list of all regional forwarding rules in the given project_id and region
    :param project_id: The project ID
    :param region: The region to pull forwarding rules from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project
    """
    req = compute.forwardingRules().list(project=project_id, region=region)
    return req.execute()


@timeit
def get_gcp_global_forwarding_rules(project_id: str, compute: Resource) -> Resource:
    """
    Return list of all global forwarding rules in the given project_id and region
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all GCP forwarding rules for a given project
    """
    req = compute.globalForwardingRules().list(project=project_id)
    return req.execute()


@timeit
def get_gcp_firewall_ingress_rules(project_id: str, compute: Resource) -> Resource:
    """
    Get ingress Firewall data for a given project
    :param project_id: The project ID to get firewalls for
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Firewall response object
    """
    req = compute.firewalls().list(project=project_id, filter='(direction="INGRESS")')
    return req.execute()


@timeit
def transform_gcp_instances(response_objects: List[Dict]) -> List[Dict]:
    """
    Process the GCP instance response objects and return a flattened list of GCP instances with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_gcp_instance_responses()
    :return: A list of GCP instances
    """
    instance_list = []
    for res in response_objects:
        prefix = res['id']
        prefix_fields = _parse_instance_uri_prefix(prefix)

        for instance in res.get('items', []):
            instance['partial_uri'] = f"{prefix}/{instance['name']}"
            instance['project_id'] = prefix_fields.project_id
            instance['zone_name'] = prefix_fields.zone_name
            instance['region'] = prefix_fields.zone_name[:-2]

            for nic in instance.get('networkInterfaces', []):
                nic['subnet_partial_uri'] = _parse_compute_full_uri_to_partial_uri(nic['subnetwork'])
                nic['vpc_partial_uri'] = _parse_compute_full_uri_to_partial_uri(nic['network'])

            instance_list.append(instance)
    return instance_list


def _parse_instance_uri_prefix(prefix: str) -> InstanceUriPrefix:
    """
    Helper function to parse a GCP prefix string of the form `projects/{project}/zones/{zone}/instances`
    :param prefix: String of the form `projects/{project}/zones/{zone}/instances`
    :return: namedtuple with fields project_id and zone_name
    """
    split_list = prefix.split('/')

    return InstanceUriPrefix(
        project_id=split_list[1],
        zone_name=split_list[3],
    )


def _parse_compute_full_uri_to_partial_uri(full_uri: str, version: str = 'v1') -> str:
    """
    Take a GCP Compute object's self_link of the form
    `https://www.googleapis.com/compute/{version}/projects/{project}/{location specifier}/{subtype}/{resource name}`
    and converts it to its partial URI `{project}/{location specifier}/{subtype}/{resource name}`.
    This is designed for GCP compute_objects that have compute/{version specifier}/ in their `self_link`s.
    :param network_full_uri: The full URI
    :param version: The version number; default to v1 since at the time of this writing v1 is the only Compute API.
    :return: Partial URI `{project}/{location specifier}/{subtype}/{resource name}`
    """
    return full_uri.split(f'compute/{version}/')[1]


def _create_gcp_network_tag_id(vpc_partial_uri: str, tag: str) -> str:
    """
    Generate an ID for a GCP network tag
    :param vpc_partial_uri: The VPC that this tag applies to
    :return: An ID for the GCP network tag
    """
    return f"{vpc_partial_uri}/tags/{tag}"


@timeit
def transform_gcp_vpcs(vpc_res: Dict) -> List[Dict]:
    """
    Transform the VPC response object for Neo4j ingestion
    :param vpc_res: The return data
    :return: List of VPCs ready for ingestion to Neo4j
    """
    vpc_list = []

    # prefix has the form `projects/{project ID}/global/networks`
    prefix = vpc_res['id']
    projectid = prefix.split('/')[1]
    for v in vpc_res.get('items', []):
        vpc = {}
        partial_uri = f"{prefix}/{v['name']}"

        vpc['id'] = partial_uri
        vpc['partial_uri'] = partial_uri
        vpc['name'] = v['name']
        vpc['self_link'] = v['selfLink']
        vpc['project_id'] = projectid
        vpc['auto_create_subnetworks'] = v.get('autoCreateSubnetworks', None)
        vpc['description'] = v.get('description', None)
        vpc['routing_config_routing_mode'] = v.get('routingConfig', {}).get('routingMode', None)

        vpc_list.append(vpc)
    return vpc_list


@timeit
def transform_gcp_subnets(subnet_res: Dict) -> List[Dict]:
    """
    Add additional fields to the subnet object to make it easier to process in `load_gcp_subnets()`.
    :param subnet_res: The response object returned from compute.subnetworks.list()
    :return: A transformed subnet_res
    """
    # The `id` in the response object has the form `projects/{project}/regions/{region}/subnetworks`.
    # We can include this in each subnet object in the list to form the partial_uri later on.
    prefix = subnet_res['id']
    projectid = prefix.split('/')[1]
    subnet_list: List[Dict] = []
    for s in subnet_res.get('items', []):
        subnet = {}

        # Has the form `projects/{project}/regions/{region}/subnetworks/{subnet_name}`
        partial_uri = f"{prefix}/{s['name']}"
        subnet['id'] = partial_uri
        subnet['partial_uri'] = partial_uri

        # Let's maintain an on-node reference to the VPC that this subnet belongs to.
        subnet['vpc_self_link'] = s['network']
        subnet['vpc_partial_uri'] = _parse_compute_full_uri_to_partial_uri(s['network'])

        subnet['name'] = s['name']
        subnet['project_id'] = projectid
        # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
        subnet['region'] = s['region'].split('/')[-1]
        subnet['gateway_address'] = s.get('gatewayAddress', None)
        subnet['ip_cidr_range'] = s.get('ipCidrRange', None)
        subnet['self_link'] = s['selfLink']
        subnet['private_ip_google_access'] = s.get('privateIpGoogleAccess', None)

        subnet_list.append(subnet)
    return subnet_list


@timeit
def transform_gcp_forwarding_rules(fwd_response: Resource) -> List[Dict]:
    """
    Add additional fields to the forwarding rule object to make it easier to process in `load_gcp_forwarding_rules()`.
    :param fwd_response: The response object returned from compute.forwardRules.list()
    :return: A transformed fwd_response
    """
    fwd_list: List[Dict] = []
    prefix = fwd_response['id']
    project_id = prefix.split('/')[1]
    for fwd in fwd_response.get('items', []):
        forwarding_rule: Dict[str, Any] = {}

        fwd_partial_uri = f"{prefix}/{fwd['name']}"
        forwarding_rule['id'] = fwd_partial_uri
        forwarding_rule['partial_uri'] = fwd_partial_uri

        forwarding_rule['project_id'] = project_id
        # Region looks like "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region name}"
        region = fwd.get('region', None)
        forwarding_rule['region'] = region.split('/')[-1] if region else None
        forwarding_rule['ip_address'] = fwd['IPAddress']
        forwarding_rule['ip_protocol'] = fwd.get('IPProtocol', None)
        forwarding_rule['allow_global_access'] = fwd.get('allowGlobalAccess', None)

        forwarding_rule['load_balancing_scheme'] = fwd.get('loadBalancingScheme', None)
        forwarding_rule['name'] = fwd['name']
        forwarding_rule['port_range'] = fwd.get('portRange', None)
        forwarding_rule['ports'] = fwd.get('ports', None)
        forwarding_rule['self_link'] = fwd['selfLink']
        target = fwd.get('target', None)
        if target:
            forwarding_rule['target'] = _parse_compute_full_uri_to_partial_uri(target)
        else:
            forwarding_rule['target'] = None

        network = fwd.get('network', None)
        if network:
            forwarding_rule['network'] = network
            forwarding_rule['network_partial_uri'] = _parse_compute_full_uri_to_partial_uri(network)

        subnetwork = fwd.get('subnetwork', None)
        if subnetwork:
            forwarding_rule['subnetwork'] = subnetwork
            forwarding_rule['subnetwork_partial_uri'] = _parse_compute_full_uri_to_partial_uri(subnetwork)

        fwd_list.append(forwarding_rule)
    return fwd_list


@timeit
def transform_gcp_firewall(fw_response: Resource) -> List[Dict]:
    """
    Adjust the firewall response objects into a format that is easy to write to Neo4j.
    Also see _transform_fw_entry and _parse_port_string_to_rule().
    :param fw_response: Firewall response object from the GCP API
    :return: List of transformed firewall rule objects.
    """
    fw_list: List[Dict] = []
    prefix = fw_response['id']
    for fw in fw_response.get('items', []):
        fw_partial_uri = f"{prefix}/{fw['name']}"
        fw['id'] = fw_partial_uri
        fw['vpc_partial_uri'] = _parse_compute_full_uri_to_partial_uri(fw['network'])

        fw['transformed_allow_list'] = []
        fw['transformed_deny_list'] = []
        # Mark whether this FW is defined on a target service account.
        # In future we will need to ingest GCP IAM objects but for now we simply mark the presence of svc accounts here.
        fw['has_target_service_accounts'] = True if 'targetServiceAccounts' in fw else False

        for allow_rule in fw.get('allowed', []):
            transformed_allow_rules = _transform_fw_entry(allow_rule, fw_partial_uri, is_allow_rule=True)
            fw['transformed_allow_list'].extend(transformed_allow_rules)

        for deny_rule in fw.get('denied', []):
            transformed_deny_rules = _transform_fw_entry(deny_rule, fw_partial_uri, is_allow_rule=False)
            fw['transformed_deny_list'].extend(transformed_deny_rules)

        fw_list.append(fw)
    return fw_list


def _transform_fw_entry(rule: Dict, fw_partial_uri: str, is_allow_rule: bool) -> List[Dict]:
    """
    Takes a rule entry from a GCP firewall object's allow or deny list and converts it to a list of one or more
    dicts representing a firewall rule for each port and port range.  This format is easier to load into Neo4j.

    Example 1 - single port range:
    Input: `{'IPProtocol': 'tcp', 'ports': ['0-65535']}, fw_id, is_allow_rule=True`
    Output: `[ {fromport: 0, toport: 65535, protocol: tcp, ruleid: fw_id/allow/0to65535tcp} ]`

    Example 2 - multiple ports with a range
    Input: `{'IPProtocol': 'tcp', 'ports': ['80', '443', '12345-12349']}, fw_id, is_allow_rule=False`
    Output: `[ {fromport: 80, toport: 80, protocol: tcp, ruleid: fw_id/deny/80tcp,
               {fromport: 443, toport: 443, protocol: tcp, ruleid: fw_id/deny/443tcp,
               {fromport: 12345, toport: 12349, protocol: tcp, ruleid: fw_id/deny/12345to12349tcp ]`

    Example 3 - ICMP (no ports)
    Input: `{'IPProtocol': 'icmp'}, fw_id, is_allow_rule=True`
    Output: `[ {fromport: None, toport: None, protocol: icmp, ruleid: fw_id/allow/icmp} ]`

    :param rule: A rule entry object
    :param fw_partial_uri: The parent GCPFirewall's unique identifier
    :param is_allow_rule: Whether the rule is an `allow` rule.  If false it is a `deny` rule.
    :return: A list of one or more transformed rules
    """
    result: List[Dict] = []
    # rule['ruleid'] = f"{fw_partial_uri}/"
    protocol = rule['IPProtocol']

    # If the protocol covered is TCP or UDP then we need to handle ports
    if protocol == 'tcp' or protocol == 'udp':

        # If ports are specified then create rules for each port and range
        if 'ports' in rule:
            for port in rule['ports']:
                rule = _parse_port_string_to_rule(port, protocol, fw_partial_uri, is_allow_rule)
                result.append(rule)
            return result

        # If ports are not specified then the rule applies to every port
        else:
            rule = _parse_port_string_to_rule('0-65535', protocol, fw_partial_uri, is_allow_rule)
            result.append(rule)
            return result

    # The protocol is  ICMP, ESP, AH, IPIP, SCTP, or proto numbers and ports don't apply
    else:
        rule = _parse_port_string_to_rule(None, protocol, fw_partial_uri, is_allow_rule)
        result.append(rule)
        return result


def _parse_port_string_to_rule(port: Optional[str], protocol: str, fw_partial_uri: str, is_allow_rule: bool) -> Dict:
    """
    Takes a string argument representing a GCP firewall rule port or port range and returns a dict that is easier to
    load into Neo4j.

    Example 1 - single port range:
    Input: `'0-65535', 'tcp', fw_id, is_allow_rule=True`
    Output: `{fromport: 0, toport: 65535, protocol: tcp, ruleid: fw_id/allow/0to65535tcp}`

    Example 2 - single port
    Input: `'80', fw_id, is_allow_rule=False`
    Output: `{fromport: 80, toport: 80, protocol: tcp, ruleid: fw_id/deny/80tcp}`

    Example 3 - ICMP (no ports)
    Input: `None, fw_id, is_allow_rule=True`
    Output: `{fromport: None, toport: None, protocol: icmp, ruleid: fw_id/allow/icmp}`

    :param port: A string representing a single port or a range of ports.  Example inputs include '22' or '12345-12349'
    :param protocol: The protocol
    :param fw_partial_uri: The partial URI of the firewall
    :param is_allow_rule: Whether the rule is an `allow` rule.  If false it is a `deny` rule.
    :return: A dict containing fromport, toport, a ruleid, and protocol
    """
    # `port` can be a range like '12345-12349' or a single port like '22'

    if port is None:
        # Keep the port range as the empty string
        port_range_str = ''
        fromport = None
        toport = None
    else:
        # Case 1 - port range: '12345-12349'.split('-') => ['12345','12349'].
        # Case 2 - single port: '22'.split('-') => ['22'].
        port_split = port.split('-')

        # Port range
        if len(port_split) == 2:
            port_range_str = f"{port_split[0]}to{port_split[1]}"
            fromport = int(port_split[0])
            toport = int(port_split[1])
        # Single port
        else:
            port_range_str = f"{port_split[0]}"
            fromport = int(port_split[0])
            toport = int(port_split[0])

    rule_type = 'allow' if is_allow_rule else 'deny'

    return {
        'ruleid': f"{fw_partial_uri}/{rule_type}/{port_range_str}{protocol}",
        'fromport': fromport,
        'toport': toport,
        'protocol': protocol,
    }


@timeit
def load_gcp_instances(neo4j_session: neo4j.Session, data: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP instance objects to Neo4j
    :param neo4j_session: The Neo4j session object
    :param data: List of GCP instances to ingest. Basically the output of
    https://cloud.google.com/compute/docs/reference/rest/v1/instances/list
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    neo4j_session.write_transaction(_load_gcp_instances_transaction, data, gcp_project_id, gcp_update_tag)

    _attach_instance_tags(neo4j_session, data, gcp_update_tag)

    # _attach_gcp_nics(neo4j_session, data, gcp_update_tag)
    # print('nics attached')

    _attach_gcp_vpc(neo4j_session, data, gcp_update_tag)


@timeit
def _load_gcp_instances_transaction(tx: neo4j.Transaction, data: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND {compute_instances_list} AS cil
        MERGE (i:Instance:GCPInstance{id:cil.id})
        ON CREATE SET i.firstseen = timestamp(),
        i.partial_uri = cil.partial_uri
        SET i.self_link = cil.selfLink,
        i.instancename = cil.name,
        i.hostname = cil.hostname,
        i.zone_name = cil.zone_name,
        i.region = cil.region,
        i.project_id = cil.project_id,
        i.status = cil.status,
        i.lastupdated = {gcp_update_tag}
        WITH i, cil

        MERGE (p:GCPProject{id:{ProjectId}})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = {gcp_update_tag}
        WITH i, p, cil

        MERGE (p)-[r:RESOURCE]->(i)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        compute_instances_list=data,
        ProjectId=gcp_project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_vpcs(neo4j_session: neo4j.Session, vpcs: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest VPCs to Neo4j
    :param neo4j_session: The Neo4j session object
    :param vpcs: List of VPCs to ingest
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    neo4j_session.write_transaction(_load_gcp_vpcs_transaction, vpcs, gcp_project_id, gcp_update_tag)


@timeit
def _load_gcp_vpcs_transaction(tx: neo4j.Transaction, vpcs: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND {vpcs_list} AS vl
        MERGE(vpc:GCPVpc{id:vl.id})
        ON CREATE SET vpc.firstseen = timestamp(),
        vpc.partial_uri = vl.partial_uri
        SET vpc.self_link = vl.self_link,
        vpc.name = vl.name,
        vpc.project_id = vl.project_id,
        vpc.auto_create_subnetworks = vl.auto_create_subnetworks,
        vpc.routing_config_routing_mode = vl.routing_config_routing_mode,
        vpc.description = vl.description,
        vpc.lastupdated = {gcp_update_tag}
        WITH vpc, vl

        MERGE(p:GCPProject{id:{ProjectId}})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = {gcp_update_tag}
        WITH vpc, p, vl

        MERGE (p)-[r:RESOURCE]->(vpc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        vpcs_list=vpcs,
        ProjectId=gcp_project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_subnets(neo4j_session: neo4j.Session, subnets: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    """
    Ingest GCP subnet data to Neo4j
    :param neo4j_session: The Neo4j session
    :param subnets: List of the subnets
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :return: Nothing
    """
    neo4j_session.write_transaction(_load_gcp_subnets_transaction, subnets, gcp_project_id, gcp_update_tag)


@timeit
def _load_gcp_subnets_transaction(tx: neo4j.Transaction, subnets: List[Dict], gcp_project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND {subnets_list} AS sl
        MERGE(subnet:GCPSubnet{id:sl.id})
        ON CREATE SET subnet.firstseen = timestamp(),
        subnet.partial_uri = sl.partial_url
        SET subnet.self_link = sl.self_link,
        subnet.project_id = sl.project_id,
        subnet.name = sl.name,
        subnet.region = sl.region,
        subnet.gateway_address = sl.gateway_address,
        subnet.ip_cidr_range = sl.ip_cidr_range,
        subnet.private_ip_google_access = sl.private_ip_google_access,
        subnet.vpc_partial_uri = sl.vpc_partial_uri,
        subnet.lastupdated = {gcp_update_tag}
        WITH subnet, sl

        MERGE(vpc:GCPVpc{id:sl.vpc_partial_uri})
        ON CREATE SET vpc.firstseen = timestamp(),
        vpc.partial_uri = sl.vpc_partial_uri
        WITH subnet, vpc, sl

        MERGE (vpc)-[r:RESOURCE]->(subnet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        subnets_list=subnets,
        ProjectId=gcp_project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_forwarding_rules(neo4j_session: neo4j.Session, fwd_rules: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest GCP forwarding rules data to Neo4j
    :param neo4j_session: The Neo4j session
    :param fwd_rules: List of forwarding rules
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :return: Nothing
    """

    query = """
        MERGE(fwd:GCPForwardingRule{id:{PartialUri}})
        ON CREATE SET fwd.firstseen = timestamp(),
        fwd.partial_uri = {PartialUri}
        SET fwd.ip_address = {IPAddress},
        fwd.ip_protocol = {IPProtocol},
        fwd.load_balancing_scheme = {LoadBalancingScheme},
        fwd.name = {Name},
        fwd.network = {NetworkPartialUri},
        fwd.port_range = {PortRange},
        fwd.ports = {Ports},
        fwd.project_id = {ProjectId},
        fwd.region = {Region},
        fwd.self_link = {SelfLink},
        fwd.subnetwork = {SubNetworkPartialUri},
        fwd.target = {TargetPartialUri},
        fwd.lastupdated = {gcp_update_tag}
    """

    for fwd in fwd_rules:
        network = fwd.get('network', None)
        subnetwork = fwd.get('subnetwork', None)

        neo4j_session.run(
            query,
            PartialUri=fwd['partial_uri'],
            IPAddress=fwd['ip_address'],
            IPProtocol=fwd['ip_protocol'],
            LoadBalancingScheme=fwd.get('load_balancing_scheme', None),
            Name=fwd['name'],
            Network=network,
            NetworkPartialUri=fwd.get('network_partial_uri', None),
            PortRange=fwd.get('port_range', None),
            Ports=fwd.get('ports', None),
            ProjectId=fwd['project_id'],
            Region=fwd.get('region', None),
            SelfLink=fwd['self_link'],
            SubNetwork=subnetwork,
            SubNetworkPartialUri=fwd.get('subnetwork_partial_uri', None),
            TargetPartialUri=fwd['target'],
            gcp_update_tag=gcp_update_tag,
        )

        if subnetwork:
            _attach_fwd_rule_to_subnet(neo4j_session, fwd, gcp_update_tag)
        elif network:
            _attach_fwd_rule_to_vpc(neo4j_session, fwd, gcp_update_tag)


@timeit
def _attach_fwd_rule_to_subnet(neo4j_session: neo4j.Session, fwd: Dict, gcp_update_tag: int) -> None:
    query = """
        MERGE(subnet:GCPSubnet{id:{SubNetworkPartialUri}})
        ON CREATE SET subnet.firstseen = timestamp(),
        subnet.partial_uri = {SubNetworkPartialUri}
        SET subnet.lastupdated = {gcp_update_tag}

        WITH subnet
        MATCH(fwd:GCPForwardingRule{id:{PartialUri}})

        MERGE(subnet)-[p:RESOURCE]->(fwd)
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = {gcp_update_tag}
    """

    neo4j_session.run(
        query,
        PartialUri=fwd['partial_uri'],
        SubNetworkPartialUri=fwd.get('subnetwork_partial_uri', None),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_fwd_rule_to_vpc(neo4j_session: neo4j.Session, fwd: Dict, gcp_update_tag: int) -> None:
    query = """
        MERGE (vpc:GCPVpc{id:{NetworkPartialUri}})
        ON CREATE SET vpc.firstseen = timestamp(),
        vpc.partial_uri = {NetworkPartialUri}

        WITH vpc
        MATCH (fwd:GCPForwardingRule{id:{PartialUri}})

        MERGE (vpc)-[r:RESOURCE]->(fwd)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """

    neo4j_session.run(
        query,
        PartialUri=fwd['partial_uri'],
        NetworkPartialUri=fwd.get('network_partial_uri', None),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_instance_tags(neo4j_session: neo4j.Session, instances: List[Resource], gcp_update_tag: int) -> None:
    """
    Attach tags to GCP instance and to the VPCs that they are defined in.
    :param neo4j_session: The session
    :param instance: The instance object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    tags = []
    for instance in instances:
        for tag in instance.get('tags', {}).get('items', []):
            for nic in instance.get('networkInterfaces', []):
                tag_id = _create_gcp_network_tag_id(nic['vpc_partial_uri'], tag)
                tags.append({
                    'id': tag_id,
                    'value': tag,
                    'instance_id': instance['partial_uri'],
                    'vpc_partial_uri': nic['vpc_partial_uri'],
                })

    neo4j_session.write_transaction(_attach_instance_tags_transaction, tags, gcp_update_tag)


@timeit
def _attach_instance_tags_transaction(tx: neo4j.Transaction, tags: List[Dict], gcp_update_tag: int) -> None:
    query = """
    UNWIND {tags_list} AS tl
        MERGE (t:GCPNetworkTag{id:tl.id})
        ON CREATE SET t.tag_id = tl.id,
        t.value = tl.value,
        t.firstseen = timestamp()
        SET t.lastupdated = {gcp_update_tag}
        WITH t, tl

        MATCH (i:GCPInstance{id:tl.instance_id})
        WITH t, i, tl

        MERGE (i)-[h:TAGGED]->(t)
        ON CREATE SET h.firstseen = timestamp()
        SET h.lastupdated = {gcp_update_tag}
        WITH t, i, tl

        MATCH (vpc:GCPVpc{id:tl.vpc_partial_uri})
        MERGE (vpc)<-[d:DEFINED_IN]-(t)
        ON CREATE SET d.firstseen = timestamp()
        SET d.lastupdated = {gcp_update_tag}
    """

    tx.run(
        query,
        tags_list=tags,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_gcp_nics(neo4j_session: neo4j.Session, instances: List[Resource], gcp_update_tag: int) -> None:
    """
    Attach GCP Network Interfaces to GCP Instances and GCP Subnets.
    Then, attach GCP Instances directly to VPCs.
    :param neo4j_session: The Neo4j session
    :param instance: The GCP instance
    :param gcp_update_tag: Timestamp to set the nodes
    :return: Nothing
    """
    nics = []
    nic_access_configs = []
    for instance in instances:
        for nic in instance.get('networkInterfaces', []):
            # Make an ID for GCPNetworkInterface nodes because GCP doesn't define one but we need to uniquely identify them
            nic_id = f"{instance['partial_uri']}/networkinterfaces/{nic['name']}"
            nics.append({
                'id': nic_id,
                'name': nic['name'],
                'instance_id': instance['partial_uri'],
                'network_ip': nic.get('networkIP'),
                'subnet_partial_uri': nic['subnet_partial_uri'],
            })

            for ac in nic.get('accessConfigs', []):
                # Make an ID for GCPNicAccessConfig nodes because GCP doesn't define one but we need to uniquely identify them
                access_config_id = f"{nic_id}/accessconfigs/{ac['type']}"
                nic_access_configs.append({
                    'id': nic_id,
                    'name': ac['name'],
                    'type': ac['type'],
                    'access_config_id': access_config_id,
                    'nat_ip': ac.get('natIP', None),
                    'set_public_ptr': ac.get('setPublicPtr', None),
                    'public_ptr_domain_name': ac.get('publicPtrDomainName', None),
                    'network_tier': ac.get('networkTier', None),
                })

    neo4j_session.write_transaction(_attach_gcp_nics_transaction, nics, gcp_update_tag)

    neo4j_session.write_transaction(_attach_gcp_nic_configs_transaction, nic_access_configs, gcp_update_tag)


@timeit
def _attach_gcp_nics_transaction(tx: neo4j.Transaction, nics: List[Dict], gcp_update_tag: int) -> None:
    query = """
    UNWIND {nics_list} AS nl
        MERGE (nic:GCPNetworkInterface:NetworkInterface{id:nl.id})
        ON CREATE SET nic.firstseen = timestamp(),
        nic.nic_id = nl.id
        SET nic.private_ip = nl.network_ip,
        nic.name = nl.name,
        nic.lastupdated = {gcp_update_tag}
        WITH nic, nl

        MATCH (i:GCPInstance{id:nl.instance_id})
        WITH nic, i, nl

        MERGE (i)-[r:NETWORK_INTERFACE]->(nic)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
        WITH nic, i, nl

        MERGE (subnet:GCPSubnet{id:nl.subnet_partial_uri})
        ON CREATE SET subnet.firstseen = timestamp(),
        subnet.partial_uri = nl.subnet_partial_uri
        SET subnet.lastupdated = {gcp_update_tag}
        WITH nic, subnet, i, nl

        MERGE (nic)-[p:PART_OF_SUBNET]->(subnet)
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        nics_list=nics,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_gcp_nic_configs_transaction(tx: neo4j.Transaction, nic_configs: List[Dict], gcp_update_tag: int) -> None:
    query = """
    UNWIND {nic_configs_list} AS ncl
        MERGE (ac:GCPNicAccessConfig{id:ncl.access_config_id})
        ON CREATE SET ac.firstseen = timestamp(),
        ac.access_config_id = ncl.access_config_id
        SET ac.type=ncl.type,
        ac.name = ncl.name,
        ac.public_ip = ncl.nat_ip,
        ac.set_public_ptr = ncl.set_public_ptr,
        ac.public_ptr_domain_name = ncl.public_ptr_domain_name,
        ac.network_tier = ncl.network_tier,
        ac.lastupdated = {gcp_update_tag}
        WITH ac, ncl

        MATCH (nic{id:ncl.id})
        WITH nic, ac, ncl

        MERGE (nic)-[r:RESOURCE]->(ac)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        nic_configs_list=nic_configs,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_gcp_vpc(neo4j_session: neo4j.Session, instances: List[Dict], gcp_update_tag: int) -> None:
    """
    Attach a GCP instance directly to a VPC
    :param neo4j_session: neo4j_session
    :param instance: The GCP instance object
    :param gcp_update_tag:
    :return: Nothing
    """
    items = []
    for instance in instances:
        items.append({
            'instance_id': instance['partial_uri']
        })

    neo4j_session.write_transaction(_attach_gcp_vpc_transaction, items, gcp_update_tag)


@timeit
def _attach_gcp_vpc_transaction(tx: neo4j.Transaction, items: List[Resource], gcp_update_tag: int) -> None:
    query = """
    UNWIND {vpc_items} AS vi
        MATCH (i:GCPInstance{id:vi.instance_id})-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
        -[p:PART_OF_SUBNET]->(sn:GCPSubnet)<-[r:RESOURCE]-(vpc:GCPVpc)
        WITH i, vi

        MERGE (i)-[m:MEMBER_OF_GCP_VPC]->(vpc)
        ON CREATE SET m.firstseen = timestamp()
        SET m.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        vpc_items=items,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_ingress_firewalls(neo4j_session: neo4j.Session, fw_list: List[Resource], gcp_project_id: str, gcp_update_tag: int) -> None:
    """
    Load the firewall list to Neo4j
    :param fw_list: The transformed list of firewalls
    :return: Nothing
    """
    neo4j_session.write_transaction(_load_gcp_ingress_firewalls_transaction, fw_list, gcp_project_id, gcp_update_tag)

    for fw in fw_list:
        _attach_firewall_rules(neo4j_session, fw, gcp_update_tag)
        _attach_target_tags(neo4j_session, fw, gcp_update_tag)


@timeit
def _load_gcp_ingress_firewalls_transaction(tx: neo4j.Transaction, fw_list: List[Resource], gcp_project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND {firewalls_list} AS fl
        MERGE (fw:GCPFirewall{id:fl.id})
        ON CREATE SET fw.firstseen = timestamp(),
        fw.partial_uri = fl.id
        SET fw.direction = fl.direction,
        fw.disabled = fl.disabled,
        fw.name = fl.name,
        fw.priority = fl.priority,
        fw.self_link = fl.selfLink,
        fw.has_target_service_accounts = fl.has_target_service_accounts,
        fw.lastupdated = {gcp_update_tag}
        WITH fw, fl

        MERGE (vpc:GCPVpc{id:fl.vpc_partial_uri})
        ON CREATE SET vpc.firstseen = timestamp(),
        vpc.partial_uri = fl.vpc_partial_uri
        SET vpc.lastupdated = {gcp_update_tag}
        WITH fw, vpc, fl

        MERGE (vpc)-[r:RESOURCE]->(fw)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        firewalls_list=fw_list,
        ProjectId=gcp_project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def _attach_firewall_rules(neo4j_session: neo4j.Session, fw: Resource, gcp_update_tag: int) -> None:
    """
    Attach the allow_rules to the Firewall object
    :param neo4j_session: The Neo4j session
    :param fw: The Firewall object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    template = Template("""
    MATCH (fw:GCPFirewall{id:{FwPartialUri}})

    MERGE (rule:IpRule:IpPermissionInbound:GCPIpRule{id:{RuleId}})
    ON CREATE SET rule.firstseen = timestamp(),
    rule.ruleid = {RuleId}
    SET rule.protocol = {Protocol},
    rule.fromport = {FromPort},
    rule.toport = {ToPort},
    rule.lastupdated = {gcp_update_tag}

    MERGE (rng:IpRange{id:{Range}})
    ON CREATE SET rng.firstseen = timestamp(),
    rng.range = {Range}
    SET rng.lastupdated = {gcp_update_tag}

    MERGE (rng)-[m:MEMBER_OF_IP_RULE]->(rule)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {gcp_update_tag}

    MERGE (fw)<-[r:$fw_rule_relationship_label]-(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """)
    for list_type in 'transformed_allow_list', 'transformed_deny_list':
        if list_type == 'transformed_allow_list':
            label = "ALLOWED_BY"
        else:
            label = "DENIED_BY"
        for rule in fw[list_type]:
            # It is possible for sourceRanges to not be specified for this rule
            # If sourceRanges is not specified then the rule must specify sourceTags.
            # Since an IP range cannot have a tag applied to it, it is ok if we don't ingest this rule.
            for ip_range in fw.get('sourceRanges', []):
                neo4j_session.run(
                    template.safe_substitute(fw_rule_relationship_label=label),
                    FwPartialUri=fw['id'],
                    RuleId=rule['ruleid'],
                    Protocol=rule['protocol'],
                    FromPort=rule.get('fromport'),
                    ToPort=rule.get('toport'),
                    Range=ip_range,
                    gcp_update_tag=gcp_update_tag,
                )


@timeit
def _attach_target_tags(neo4j_session: neo4j.Session, fw: Resource, gcp_update_tag: int) -> None:
    """
    Attach target tags to the firewall object
    :param neo4j_session: The neo4j session
    :param fw: The firewall object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    query = """
    MATCH (fw:GCPFirewall{id:{FwPartialUri}})

    MERGE (t:GCPNetworkTag{id:{TagId}})
    ON CREATE SET t.firstseen = timestamp(),
    t.tag_id = {TagId},
    t.value = {TagValue}
    SET t.lastupdated = {gcp_update_tag}

    MERGE (fw)-[h:TARGET_TAG]->(t)
    ON CREATE SET h.firstseen = timestamp()
    SET h.lastupdated = {gcp_update_tag}
    """
    for tag in fw.get('targetTags', []):
        tag_id = _create_gcp_network_tag_id(fw['vpc_partial_uri'], tag)
        neo4j_session.run(
            query,
            FwPartialUri=fw['id'],
            TagId=tag_id,
            TagValue=tag,
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP instance nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_instance_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_vpcs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP VPC nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_vpc_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP VPC subnet nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_vpc_subnet_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_forwarding_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP forwarding rules and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_forwarding_rules_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_firewall_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out of date GCP firewalls and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_firewall_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_gcp_instances(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, zones: Optional[List[Dict]],
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Get GCP instances using the Compute resource object, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session object
    :param compute: The GCP Compute resource object
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param zones: The list of all zone names that are enabled for this project; this is the output of
    `get_zones_in_project()`
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    instance_responses = get_gcp_instance_responses(project_id, zones, compute)
    instance_list = transform_gcp_instances(instance_responses)
    load_gcp_instances(neo4j_session, instance_list, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_instances(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_vpcs(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP VPCs, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    vpc_res = get_gcp_vpcs(project_id, compute)
    vpcs = transform_gcp_vpcs(vpc_res)
    load_gcp_vpcs(neo4j_session, vpcs, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_vpcs(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_subnets(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: List[str], gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for r in regions:
        subnet_res = get_gcp_subnets(project_id, r, compute)
        subnets = transform_gcp_subnets(subnet_res)
        load_gcp_subnets(neo4j_session, subnets, project_id, gcp_update_tag)
        # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
        cleanup_gcp_subnets(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_forwarding_rules(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: List[str], gcp_update_tag: int,

    common_job_parameters: Dict,
) -> None:
    """
    Sync GCP Both Global and Regional Forwarding Rules, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param regions: List of regions.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    global_fwd_response = get_gcp_global_forwarding_rules(project_id, compute)
    forwarding_rules = transform_gcp_forwarding_rules(global_fwd_response)
    load_gcp_forwarding_rules(neo4j_session, forwarding_rules, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_forwarding_rules(neo4j_session, common_job_parameters)

    for r in regions:
        fwd_response = get_gcp_regional_forwarding_rules(project_id, r, compute)
        forwarding_rules = transform_gcp_forwarding_rules(fwd_response)
        load_gcp_forwarding_rules(neo4j_session, forwarding_rules, gcp_update_tag)
        # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
        cleanup_gcp_forwarding_rules(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_firewall_rules(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync GCP firewalls
    :param neo4j_session: The Neo4j session
    :param compute: The Compute resource object
    :param project_id: The project ID that the firewalls are in
    :param common_job_parameters: dict of other job params to pass to Neo4j
    :return: Nothing
    """
    fw_response = get_gcp_firewall_ingress_rules(project_id, compute)
    fw_list = transform_gcp_firewall(fw_response)
    load_gcp_ingress_firewalls(neo4j_session, fw_list, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_firewall_rules(neo4j_session, common_job_parameters)


def _zones_to_regions(zones: List[str]) -> List[Set]:
    """
    Return list of regions from the input list of zones
    :param zones: List of zones. This is the output from `get_zones_in_project()`.
    :return: List of regions available to the project
    """
    regions = set()
    for zone in zones:
        # Chop off the last 2 chars to turn the zone to a region
        region = zone['name'][:-2]     # type: ignore
        regions.add(region)
    return list(regions)     # type: ignore


def sync(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: dict, regions: List[str],
) -> None:
    """
    Sync all objects that we need the GCP Compute resource object for.
    :param neo4j_session: The Neo4j session object
    :param compute: The GCP Compute resource object
    :param project_id: The project ID number to sync.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    logger.info("Syncing Compute objects for project %s.", project_id)

    # regions are calculated in init file as a common placeholder
    zones = get_zones_in_project(project_id, compute)
    # Only pull additional assets for this project if the Compute API is enabled
    if zones is None:
        return
    else:
        regions = _zones_to_regions(zones)

    logger.info("Syncing Compute VPCs for project %s.", project_id)
    sync_gcp_vpcs(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)

    logger.info("Syncing Compute Firewalls for project %s.", project_id)
    sync_gcp_firewall_rules(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)

    logger.info("Syncing Compute Subnets for project %s.", project_id)
    sync_gcp_subnets(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)

    logger.info("Syncing Compute Instances for project %s.", project_id)
    sync_gcp_instances(neo4j_session, compute, project_id, zones, gcp_update_tag, common_job_parameters)

    logger.info("Syncing Compute Forwarding Rules for project %s.", project_id)
    sync_gcp_forwarding_rules(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)

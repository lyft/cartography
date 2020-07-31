# Google Compute Engine API-centric functions
# https://cloud.google.com/compute/docs/concepts
import json
import logging
from collections import namedtuple
from string import Template

from googleapiclient.discovery import HttpError

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
InstanceUriPrefix = namedtuple('InstanceUriPrefix', 'zone_name project_id')


def _get_error_reason(http_error):
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
def get_zones_in_project(project_id, compute, max_results=None):
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
def get_gcp_instance_responses(project_id, zones, compute):
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
    response_objects = []
    for zone in zones:
        req = compute.instances().list(project=project_id, zone=zone['name'])
        res = req.execute()
        response_objects.append(res)
    return response_objects


@timeit
def get_gcp_subnets(projectid, region, compute):
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
def get_gcp_vpcs(projectid, compute):
    """
    Get VPC data for given project
    :param projectid: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: VPC response object
    """
    req = compute.networks().list(project=projectid)
    return req.execute()


@timeit
def get_gcp_firewall_ingress_rules(project_id, compute):
    """
    Get ingress Firewall data for a given project
    :param project_id: The project ID to get firewalls for
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Firewall response object
    """
    req = compute.firewalls().list(project=project_id, filter='(direction="INGRESS")')
    return req.execute()


@timeit
def transform_gcp_instances(response_objects):
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

            for nic in instance.get('networkInterfaces', []):
                nic['subnet_partial_uri'] = _parse_compute_full_uri_to_partial_uri(nic['subnetwork'])
                nic['vpc_partial_uri'] = _parse_compute_full_uri_to_partial_uri(nic['network'])

            instance_list.append(instance)
    return instance_list


def _parse_instance_uri_prefix(prefix):
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


def _parse_compute_full_uri_to_partial_uri(full_uri, version='v1'):
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


def _create_gcp_network_tag_id(vpc_partial_uri, tag):
    """
    Generate an ID for a GCP network tag
    :param vpc_partial_uri: The VPC that this tag applies to
    :return: An ID for the GCP network tag
    """
    return f"{vpc_partial_uri}/tags/{tag}"


@timeit
def transform_gcp_vpcs(vpc_res):
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
def transform_gcp_subnets(subnet_res):
    """
    Add additional fields to the subnet object to make it easier to process in `load_gcp_subnets()`.
    :param subnet_res: The response object returned from compute.subnetworks.list()
    :return: A transformed subnet_res
    """
    # The `id` in the response object has the form `projects/{project}/regions/{region}/subnetworks`.
    # We can include this in each subnet object in the list to form the partial_uri later on.
    prefix = subnet_res['id']
    projectid = prefix.split('/')[1]
    subnet_list = []
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
def transform_gcp_firewall(fw_response):
    """
    Adjust the firewall response objects into a format that is easy to write to Neo4j.
    Also see _transform_fw_entry and _parse_port_string_to_rule().
    :param fw_response: Firewall response object from the GCP API
    :return: List of transformed firewall rule objects.
    """
    fw_list = []
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


def _transform_fw_entry(rule, fw_partial_uri, is_allow_rule):
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
    result = []
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


def _parse_port_string_to_rule(port, protocol, fw_partial_uri, is_allow_rule):
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
def load_gcp_instances(neo4j_session, data, gcp_update_tag):
    """
    Ingest GCP instance objects to Neo4j
    :param neo4j_session: The Neo4j session object
    :param data: List of GCP instances to ingest. Basically the output of
    https://cloud.google.com/compute/docs/reference/rest/v1/instances/list
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (p:GCPProject{id:{ProjectId}})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {gcp_update_tag}

    MERGE (i:Instance:GCPInstance{id:{PartialUri}})
    ON CREATE SET i.firstseen = timestamp(),
    i.partial_uri = {PartialUri}
    SET i.self_link = {SelfLink},
    i.instancename = {InstanceName},
    i.hostname = {Hostname},
    i.zone_name = {ZoneName},
    i.project_id = {ProjectId},
    i.status = {Status},
    i.lastupdated = {gcp_update_tag}
    WITH i, p

    MERGE (p)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for instance in data:
        neo4j_session.run(
            query,
            ProjectId=instance['project_id'],
            PartialUri=instance['partial_uri'],
            SelfLink=instance['selfLink'],
            InstanceName=instance['name'],
            ZoneName=instance['zone_name'],
            Hostname=instance.get('hostname', None),
            Status=instance['status'],
            gcp_update_tag=gcp_update_tag,
        )
        _attach_instance_tags(neo4j_session, instance, gcp_update_tag)
        _attach_gcp_nics(neo4j_session, instance, gcp_update_tag)
        _attach_gcp_vpc(neo4j_session, instance['partial_uri'], gcp_update_tag)


@timeit
def load_gcp_vpcs(neo4j_session, vpcs, gcp_update_tag):
    """
    Ingest VPCs to Neo4j
    :param neo4j_session: The Neo4j session object
    :param vpcs: List of VPCs to ingest
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE(p:GCPProject{id:{ProjectId}})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {gcp_update_tag}

    MERGE(vpc:GCPVpc{id:{PartialUri}})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = {PartialUri}
    SET vpc.self_link = {SelfLink},
    vpc.name = {VpcName},
    vpc.project_id = {ProjectId},
    vpc.auto_create_subnetworks = {AutoCreateSubnetworks},
    vpc.routing_config_routing_mode = {RoutingMode},
    vpc.description = {Description},
    vpc.lastupdated = {gcp_update_tag}

    MERGE (p)-[r:RESOURCE]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for vpc in vpcs:
        neo4j_session.run(
            query,
            ProjectId=vpc['project_id'],
            PartialUri=vpc['partial_uri'],
            SelfLink=vpc['self_link'],
            VpcName=vpc['name'],
            AutoCreateSubnetworks=vpc['auto_create_subnetworks'],
            RoutingMode=vpc['routing_config_routing_mode'],
            Description=vpc['description'],
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_subnets(neo4j_session, subnets, gcp_update_tag):
    """
    Ingest GCP subnet data to Neo4j
    :param neo4j_session: The Neo4j session
    :param subnets: List of the subnets
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE(vpc:GCPVpc{id:{VpcPartialUri}})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = {VpcPartialUri}

    MERGE(subnet:GCPSubnet{id:{PartialUri}})
    ON CREATE SET subnet.firstseen = timestamp(),
    subnet.partial_uri = {PartialUri}
    SET subnet.self_link = {SubnetSelfLink},
    subnet.project_id = {ProjectId},
    subnet.name = {SubnetName},
    subnet.region = {Region},
    subnet.gateway_address = {GatewayAddress},
    subnet.ip_cidr_range = {IpCidrRange},
    subnet.private_ip_google_access = {PrivateIpGoogleAccess},
    subnet.vpc_partial_uri = {VpcPartialUri},
    subnet.lastupdated = {gcp_update_tag}

    MERGE (vpc)-[r:RESOURCE]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for s in subnets:
        neo4j_session.run(
            query,
            VpcPartialUri=s['vpc_partial_uri'],
            VpcSelfLink=s['vpc_self_link'],
            PartialUri=s['partial_uri'],
            SubnetSelfLink=s['self_link'],
            ProjectId=s['project_id'],
            SubnetName=s['name'],
            Region=s['region'],
            GatewayAddress=s['gateway_address'],
            IpCidrRange=s['ip_cidr_range'],
            PrivateIpGoogleAccess=s['private_ip_google_access'],
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def _attach_instance_tags(neo4j_session, instance, gcp_update_tag):
    """
    Attach tags to GCP instance and to the VPCs that they are defined in.
    :param neo4j_session: The session
    :param instance: The instance object
    :param gcp_update_tag: The timestamp
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id:{InstanceId}})

    MERGE (t:GCPNetworkTag{id:{TagId}})
    ON CREATE SET t.tag_id = {TagId},
    t.value = {TagValue},
    t.firstseen = timestamp()
    SET t.lastupdated = {gcp_update_tag}

    MERGE (i)-[h:TAGGED]->(t)
    ON CREATE SET h.firstseen = timestamp()
    SET h.lastupdated = {gcp_update_tag}

    WITH t
    MATCH (vpc:GCPVpc{id:{VpcPartialUri}})

    MERGE (vpc)<-[d:DEFINED_IN]-(t)
    ON CREATE SET d.firstseen = timestamp()
    SET d.lastupdated = {gcp_update_tag}
    """
    for tag in instance.get('tags', {}).get('items', []):
        for nic in instance.get('networkInterfaces', []):
            tag_id = _create_gcp_network_tag_id(nic['vpc_partial_uri'], tag)
            neo4j_session.run(
                query,
                InstanceId=instance['partial_uri'],
                TagId=tag_id,
                TagValue=tag,
                VpcPartialUri=nic['vpc_partial_uri'],
                gcp_update_tag=gcp_update_tag,
            )


@timeit
def _attach_gcp_nics(neo4j_session, instance, gcp_update_tag):
    """
    Attach GCP Network Interfaces to GCP Instances and GCP Subnets.
    Then, attach GCP Instances directly to VPCs.
    :param neo4j_session: The Neo4j session
    :param instance: The GCP instance
    :param gcp_update_tag: Timestamp to set the nodes
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id:{InstanceId}})
    MERGE (nic:GCPNetworkInterface:NetworkInterface{id:{NicId}})
    ON CREATE SET nic.firstseen = timestamp(),
    nic.nic_id = {NicId}
    SET nic.private_ip = {NetworkIP},
    nic.name = {NicName},
    nic.lastupdated = {gcp_update_tag}

    MERGE (i)-[r:NETWORK_INTERFACE]->(nic)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}

    MERGE (subnet:GCPSubnet{id:{SubnetPartialUri}})
    ON CREATE SET subnet.firstseen = timestamp(),
    subnet.partial_uri = {SubnetPartialUri}
    SET subnet.lastupdated = {gcp_update_tag}

    MERGE (nic)-[p:PART_OF_SUBNET]->(subnet)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {gcp_update_tag}
    """
    for nic in instance.get('networkInterfaces', []):
        # Make an ID for GCPNetworkInterface nodes because GCP doesn't define one but we need to uniquely identify them
        nic_id = f"{instance['partial_uri']}/networkinterfaces/{nic['name']}"
        neo4j_session.run(
            query,
            InstanceId=instance['partial_uri'],
            NicId=nic_id,
            NetworkIP=nic.get('networkIP'),
            NicName=nic['name'],
            gcp_update_tag=gcp_update_tag,
            SubnetPartialUri=nic['subnet_partial_uri'],
        )
        _attach_gcp_nic_access_configs(neo4j_session, nic_id, nic, gcp_update_tag)


@timeit
def _attach_gcp_nic_access_configs(neo4j_session, nic_id, nic, gcp_update_tag):
    """
    Attach an access configuration to the GCP NIC.
    :param neo4j_session: The Neo4j session
    :param instance: The GCP instance
    :param gcp_update_tag: The timestamp to set updated nodes to
    :return: Nothing
    """
    query = """
    MATCH (nic{id:{NicId}})
    MERGE (ac:GCPNicAccessConfig{id:{AccessConfigId}})
    ON CREATE SET ac.firstseen = timestamp(),
    ac.access_config_id = {AccessConfigId}
    SET ac.type={Type},
    ac.name = {Name},
    ac.public_ip = {NatIP},
    ac.set_public_ptr = {SetPublicPtr},
    ac.public_ptr_domain_name = {PublicPtrDomainName},
    ac.network_tier = {NetworkTier},
    ac.lastupdated = {gcp_update_tag}

    MERGE (nic)-[r:RESOURCE]->(ac)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for ac in nic.get('accessConfigs', []):
        # Make an ID for GCPNicAccessConfig nodes because GCP doesn't define one but we need to uniquely identify them
        access_config_id = f"{nic_id}/accessconfigs/{ac['type']}"
        neo4j_session.run(
            query,
            NicId=nic_id,
            AccessConfigId=access_config_id,
            Type=ac['type'],
            Name=ac['name'],
            NatIP=ac.get('natIP', None),
            SetPublicPtr=ac.get('setPublicPtr', None),
            PublicPtrDomainName=ac.get('publicPtrDomainName', None),
            NetworkTier=ac.get('networkTier', None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def _attach_gcp_vpc(neo4j_session, instance_id, gcp_update_tag):
    """
    Attach a GCP instance directly to a VPC
    :param neo4j_session: neo4j_session
    :param instance: The GCP instance object
    :param gcp_update_tag:
    :return: Nothing
    """
    query = """
    MATCH (i:GCPInstance{id:{InstanceId}})-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
          -[p:PART_OF_SUBNET]->(sn:GCPSubnet)<-[r:RESOURCE]-(vpc:GCPVpc)
    MERGE (i)-[m:MEMBER_OF_GCP_VPC]->(vpc)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {gcp_update_tag}
    """
    neo4j_session.run(
        query,
        InstanceId=instance_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gcp_ingress_firewalls(neo4j_session, fw_list, gcp_update_tag):
    """
    Load the firewall list to Neo4j
    :param fw_list: The transformed list of firewalls
    :return: Nothing
    """
    query = """
    MERGE (fw:GCPFirewall{id:{FwPartialUri}})
    ON CREATE SET fw.firstseen = timestamp(),
    fw.partial_uri = {FwPartialUri}
    SET fw.direction = {Direction},
    fw.disabled = {Disabled},
    fw.name = {Name},
    fw.priority = {Priority},
    fw.self_link = {SelfLink},
    fw.has_target_service_accounts = {HasTargetServiceAccounts},
    fw.lastupdated = {gcp_update_tag}

    MERGE (vpc:GCPVpc{id:{VpcPartialUri}})
    ON CREATE SET vpc.firstseen = timestamp(),
    vpc.partial_uri = {VpcPartialUri}
    SET vpc.lastupdated = {gcp_update_tag}

    MERGE (vpc)-[r:RESOURCE]->(fw)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for fw in fw_list:
        neo4j_session.run(
            query,
            FwPartialUri=fw['id'],
            Direction=fw['direction'],
            Disabled=fw['disabled'],
            Name=fw['name'],
            Priority=fw['priority'],
            SelfLink=fw['selfLink'],
            VpcPartialUri=fw['vpc_partial_uri'],
            HasTargetServiceAccounts=fw['has_target_service_accounts'],
            gcp_update_tag=gcp_update_tag,
        )
        _attach_firewall_rules(neo4j_session, fw, gcp_update_tag)
        _attach_target_tags(neo4j_session, fw, gcp_update_tag)


@timeit
def _attach_firewall_rules(neo4j_session, fw, gcp_update_tag):
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
def _attach_target_tags(neo4j_session, fw, gcp_update_tag):
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
def cleanup_gcp_instances(neo4j_session, common_job_parameters):
    """
    Delete out-of-date GCP instance nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_instance_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_vpcs(neo4j_session, common_job_parameters):
    """
    Delete out-of-date GCP VPC nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_vpc_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_subnets(neo4j_session, common_job_parameters):
    """
    Delete out-of-date GCP VPC subnet nodes and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_vpc_subnet_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_firewall_rules(neo4j_session, common_job_parameters):
    """
    Delete out of date GCP firewalls and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job('gcp_compute_firewall_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_gcp_instances(neo4j_session, compute, project_id, zones, gcp_update_tag, common_job_parameters):
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
    load_gcp_instances(neo4j_session, instance_list, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_instances(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_vpcs(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters):
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
    load_gcp_vpcs(neo4j_session, vpcs, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_vpcs(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_subnets(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters):
    for r in regions:
        subnet_res = get_gcp_subnets(project_id, r, compute)
        subnets = transform_gcp_subnets(subnet_res)
        load_gcp_subnets(neo4j_session, subnets, gcp_update_tag)
        # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
        cleanup_gcp_subnets(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_firewall_rules(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters):
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
    load_gcp_ingress_firewalls(neo4j_session, fw_list, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_firewall_rules(neo4j_session, common_job_parameters)


def _zones_to_regions(zones):
    """
    Return list of regions from the input list of zones
    :param zones: List of zones. This is the output from `get_zones_in_project()`.
    :return: List of regions available to the project
    """
    regions = set()
    for z in zones:
        # Chop off the last 2 chars to turn the zone to a region
        r = z['name'][:-2]
        regions.add(r)
    return list(regions)


def sync(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters):
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
    zones = get_zones_in_project(project_id, compute)
    # Only pull additional assets for this project if the Compute API is enabled
    if zones is None:
        return
    else:
        regions = _zones_to_regions(zones)
        sync_gcp_vpcs(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
        sync_gcp_firewall_rules(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
        sync_gcp_subnets(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)
        sync_gcp_instances(neo4j_session, compute, project_id, zones, gcp_update_tag, common_job_parameters)

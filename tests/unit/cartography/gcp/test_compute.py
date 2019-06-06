import cartography.intel.gcp.compute
from tests.data.gcp.compute import VPC_RESPONSE, VPC_SUBNET_RESPONSE


def test_transform_gcp_vpcs():
    """
    Ensure that transform_gcp_vpcs() returns a list of VPCs, computes correct partial_uris, and parses the nested
    objects correctly.
    """
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(VPC_RESPONSE)
    assert len(vpc_list) == 1

    vpc = vpc_list[0]
    assert vpc['partial_uri'] == 'projects/project-abc/global/networks/default'
    assert vpc['routing_config_routing_mode'] == 'REGIONAL'


def test_transform_gcp_subnets():
    """
    Ensure that transform_gcp_subnets() returns a list of subnets with correct partial_uris and tests for the presence
    of some key members.
    """
    subnet_list = cartography.intel.gcp.compute.transform_gcp_subnets(VPC_SUBNET_RESPONSE)
    assert len(subnet_list) == 1

    subnet = subnet_list[0]
    assert subnet['ip_cidr_range'] == '10.0.0.0/20'
    assert subnet['partial_uri'] == 'projects/project-abc/regions/europe-west2/subnetworks/default'
    assert subnet['region'] == 'europe-west2'
    assert not subnet['private_ip_google_access']


def test_parse_compute_full_uri_to_partial_uri():
    subnet_uri = 'https://www.googleapis.com/compute/v1/projects/project-abc/regions/europe-west2/subnetworks/default'
    inst_uri = 'https://www.googleapis.com/compute/v1/projects/project-abc/zones/europe-west2-b/disks/instance-1'
    vpc_uri = 'https://www.googleapis.com/compute/v1/projects/project-abc/global/networks/default'

    assert cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(subnet_uri) == \
        'projects/project-abc/regions/europe-west2/subnetworks/default'
    assert cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(inst_uri) == \
        'projects/project-abc/zones/europe-west2-b/disks/instance-1'
    assert cartography.intel.gcp.compute._parse_compute_full_uri_to_partial_uri(vpc_uri) == \
        'projects/project-abc/global/networks/default'

import pytest
import cartography.intel.gcp.compute
import tests.data.gcp.compute


TEST_UPDATE_TAG = 123456789


@pytest.fixture()
def load_compute_objects(neo4j_session):
    """
    Ensure the test neo4j instance has the dummy data that we need for the integration tests
    :param neo4j_session: The neo4j session fixture
    :return: Nothing
    """
    # Load VPCs
    vpc_res = tests.data.gcp.compute.VPC_RESPONSE
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(vpc_res)
    cartography.intel.gcp.compute.load_gcp_vpcs(neo4j_session, vpc_list, TEST_UPDATE_TAG)

    # Load subnets
    subnet_res = tests.data.gcp.compute.VPC_SUBNET_RESPONSE
    subnet_list = cartography.intel.gcp.compute.transform_gcp_subnets(subnet_res)
    cartography.intel.gcp.compute.load_gcp_subnets(neo4j_session, subnet_list, TEST_UPDATE_TAG)

    # Load the Instance, NIC, and AccessConfig data
    instance_responses = [tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE]
    instance_list = cartography.intel.gcp.compute.transform_gcp_instances(instance_responses)
    cartography.intel.gcp.compute.load_gcp_instances(neo4j_session, instance_list, TEST_UPDATE_TAG)


def test_load_vpcs(load_compute_objects, neo4j_session):
    """
    Test that we can correctly transform and load VPC nodes to Neo4j
    """
    query = """
    MATCH(vpc:GCPVpc{id:{VpcId}})
    RETURN vpc.id, vpc.partial_uri, vpc.auto_create_subnetworks
    """
    expected_vpc_id = 'projects/project-abc/global/networks/default'
    nodes = neo4j_session.run(
        query,
        VpcId=expected_vpc_id
    )
    actual_nodes = set([(n['vpc.id'], n['vpc.partial_uri'], n['vpc.auto_create_subnetworks']) for n in nodes])
    expected_nodes = set([
        (expected_vpc_id, expected_vpc_id, True)
    ])
    assert actual_nodes == expected_nodes


def test_vpc_to_subnets(load_compute_objects, neo4j_session):
    """
    Ensure that subnets are connected to VPCs.
    """
    query = """
    MATCH(vpc:GCPVpc{id:{VpcId}})-[:RESOURCE]->(subnet:GCPSubnet)
    RETURN vpc.id, subnet.id, subnet.region, subnet.gateway_address, subnet.ip_cidr_range,
    subnet.private_ip_google_access
    """
    expected_vpc_id = 'projects/project-abc/global/networks/default'
    nodes = neo4j_session.run(
        query,
        VpcId=expected_vpc_id
    )
    actual_nodes = set([(
        n['vpc.id'],
        n['subnet.id'],
        n['subnet.region'],
        n['subnet.gateway_address'],
        n['subnet.ip_cidr_range'],
        n['subnet.private_ip_google_access']
    ) for n in nodes])

    expected_nodes = set([
        ('projects/project-abc/global/networks/default',
         'projects/project-abc/regions/europe-west2/subnetworks/default',
         'europe-west2',
         '10.0.0.1',
         '10.0.0.0/20',
         False)
    ])
    assert actual_nodes == expected_nodes


def test_load_gcp_instances_and_network_objects(load_compute_objects, neo4j_session):
    """
    Ensure that we can correctly transform and load GCP instances.
    """
    instance_query = """
    MATCH(i:GCPInstance)
    RETURN i.id, i.zone_name, i.project_id, i.hostname
    """
    nodes = neo4j_session.run(instance_query)
    actual_nodes = set([(n['i.id'], n['i.zone_name'], n['i.project_id'], n['i.hostname']) for n in nodes])
    expected_nodes = set([
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1-test', 'europe-west2-b', 'project-abc', None),
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1', 'europe-west2-b', 'project-abc', None)
    ])
    assert actual_nodes == expected_nodes


def test_load_network_interfaces(load_compute_objects, neo4j_session):
    """
    Ensure the network interfaces are attached to GCP instances.
    """
    nic_query = """
    MATCH(i:GCPInstance)-[r:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)
    return r.lastupdated, nic.nic_id, nic.private_ip
    """
    objects = neo4j_session.run(nic_query)
    actual_nodes = set([(o['nic.nic_id'], o['nic.private_ip'], o['r.lastupdated']) for o in objects])
    expected_nodes = set([
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0',
         '10.0.0.3',
         TEST_UPDATE_TAG),
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0',
         '10.0.0.2',
         TEST_UPDATE_TAG)
    ])
    assert actual_nodes == expected_nodes


def test_load_access_configs(load_compute_objects, neo4j_session):
    """
    Ensure the access configs are attached to the network interfaces
    """
    ac_query = """
    MATCH (nic:GCPNetworkInterface)-[r:RESOURCE]->(ac:GCPNicAccessConfig)
    return nic.nic_id, ac.access_config_id, ac.public_ip
    """
    nodes = neo4j_session.run(ac_query)

    nic_id1 = 'projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0'
    ac_id1 = f"{nic_id1}/accessconfigs/ONE_TO_ONE_NAT"
    nic_id2 = 'projects/project-abc/zones/europe-west2-b/instances/instance-1/networkinterfaces/nic0'
    ac_id2 = f"{nic_id2}/accessconfigs/ONE_TO_ONE_NAT"

    actual_nodes = set([(n['nic.nic_id'], n['ac.access_config_id'], n['ac.public_ip']) for n in nodes])
    print(actual_nodes)
    expected_nodes = set([
        (nic_id1, ac_id1, '1.3.4.5'),
        (nic_id2, ac_id2, '1.2.3.4')
    ])
    print(expected_nodes)
    assert actual_nodes == expected_nodes


def test_nic_to_subnet_connectivity(load_compute_objects, neo4j_session):
    """
    Ensure that network interfaces are attached to subnets
    """
    subnet_query = """
    MATCH (nic:GCPNetworkInterface{id:{NicId}})-[:PART_OF_SUBNET]->(subnet:GCPSubnet)
    return nic.nic_id, nic.private_ip, subnet.id,  subnet.gateway_address, subnet.ip_cidr_range
    """
    nodes = neo4j_session.run(
        subnet_query,
        NicId='projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0'
    )
    actual_nodes = set([(
        n['nic.nic_id'],
        n['nic.private_ip'],
        n['subnet.id'],
        n['subnet.gateway_address'],
        n['subnet.ip_cidr_range']
    ) for n in nodes])
    expected_nodes = set([(
        'projects/project-abc/zones/europe-west2-b/instances/instance-1-test/networkinterfaces/nic0',
        '10.0.0.3',
        'projects/project-abc/regions/europe-west2/subnetworks/default',
        '10.0.0.1',
        '10.0.0.0/20'
    )])
    print(actual_nodes)
    print(expected_nodes)
    assert actual_nodes == expected_nodes

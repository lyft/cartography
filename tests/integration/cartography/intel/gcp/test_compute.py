# import pytest
import cartography.intel.gcp.compute
import tests.data.gcp.compute


TEST_UPDATE_TAG = 123456789

#
# @pytest.fixture()
# def load_vpcs():
#


def test_load_vpcs(neo4j_session):
    """
    Test that we can correctly load VPC nodes to Neo4j and get expected data
    :param neo4j_session: The Neo4j session
    :return: Nothing
    """
    vpc_res = tests.data.gcp.compute.VPC_RESPONSE
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(vpc_res)
    cartography.intel.gcp.compute.load_gcp_vpcs(neo4j_session, vpc_list, TEST_UPDATE_TAG)

    query = """
    MATCH(vpc:GCPVpc{id:{VpcId}}) RETURN vpc.id, vpc.partial_uri, vpc.auto_create_subnetworks
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


def test_load_instances_and_network_objects(neo4j_session):
    """
    Ensure we can load VPC nodes and a GCP instance and correctly connect it to the VPC through network interfaces,
    access configs, and subnets.
    :param neo4j_session: The neo4j session
    :return: Nothing
    """
    # Load the VPC data
    vpc_res = tests.data.gcp.compute.VPC_RESPONSE
    vpc_list = cartography.intel.gcp.compute.transform_gcp_vpcs(vpc_res)
    cartography.intel.gcp.compute.load_gcp_vpcs(neo4j_session, vpc_list, TEST_UPDATE_TAG)

    # Load the Instance, NIC, and AccessConfig data
    instance_responses = [tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE]
    instance_list = cartography.intel.gcp.compute.transform_gcp_instances(instance_responses)
    cartography.intel.gcp.compute.load_gcp_instances(neo4j_session, instance_list, TEST_UPDATE_TAG)

    # Ensure the instances exist
    instance_query = """MATCH(i:GCPInstance) RETURN i.id, i.zone_name, i.project_id, i.hostname"""
    nodes = neo4j_session.run(instance_query)
    actual_nodes = set([(n['i.id'], n['i.zone_name'], n['i.project_id'], n['i.hostname']) for n in nodes])
    expected_nodes = set([
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1-test', 'europe-west2-b', 'project-abc', None),
        ('projects/project-abc/zones/europe-west2-b/instances/instance-1', 'europe-west2-b', 'project-abc', None)
    ])
    assert actual_nodes == expected_nodes

    # Ensure the network interfaces are attached
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

    # Ensure the access configs are attached to the network interfaces
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
    #
    # Ensure that the network interfaces are attached to subnets
    # subnet_query = """
    # MATCH (nic:GCPNetworkInterface)-[:PART_OF_SUBNET]->(subnet:GCPSubnet)
    # return nic.nic_id, subnet.
    # """

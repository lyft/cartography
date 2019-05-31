import cartography.intel.gcp.compute
import tests.data.gcp.compute

TEST_UPDATE_TAG = 123456789


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


def test_load_vpcs_and_instances_nics_subnets_accessconfigs(neo4j_session):
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

    # Load the instance data
    instance_responses = [tests.data.gcp.compute.GCP_LIST_INSTANCES_RESPONSE]
    instance_list = cartography.intel.gcp.compute.transform_gcp_instances(instance_responses)

    # Now load in the instance->NIC, accessconfig, subnet data
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

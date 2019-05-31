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

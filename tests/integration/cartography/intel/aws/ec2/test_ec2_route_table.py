import cartography.intel.aws.ec2.route_tables
import tests.data.aws.ec2.route_tables
import tests.data.aws.ec2.instances
import cartography.intel.aws.ec2.instances
import cartography.intel.aws.ec2.subnets
import tests.data.aws.ec2.subnets

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


def test_load_route_tables(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES
    cartography.intel.aws.ec2.route_tables.load_route_tables(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {'route_table-2', 'route_table-1'}

    nodes = neo4j_session.run(
        """
        MATCH (s:EC2RouteTable) RETURN s.id;
        """
    )
    actual_nodes = {n['s.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_route_tables_relationships(neo4j_session):
    # data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES
    # cartography.intel.aws.ec2.route_tables.load_route_tables(
    #     neo4j_session,
    #     data,
    #     TEST_ACCOUNT_ID,
    #     TEST_UPDATE_TAG
    # )
    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {

    }

    # nodes = neo4j_session.run(
    #     """
    #     MATCH (snet:EC2Subnet) return snet.subnetid
    #     """,
    # )

    nodes = neo4j_session.run(
        """
        MATCH (instance:EC2Instance) return instance.id
        """,
    )

    # nodes = neo4j_session.run(
    #     """
    #     MATCH (snet:EC2Subnet)<-[:PART_OF_SUBNET]-(instance:EC2Instance) return instance.id, snet.subnetid
    #     """,
    # )
    actual_nodes = {
        (
            n['instance.id'],
            # n['snet.subnetid'],
            # n['rtab.id'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

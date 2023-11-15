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


def test_load_route_tables_explicit_relationships(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES
    cartography.intel.aws.ec2.route_tables.load_route_tables(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )

    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
        "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instance_data(
        neo4j_session,
        data,
         "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('i-02',
         'subnet-020b2f3928f190ce8',
         'route_table-1'),
        ('i-03',
         'subnet-0fa9c8fa7cb241479',
         'route_table-1'),
        ('i-04',
         'subnet-0773409557644dca4',
         'route_table-2'),
    }

    nodes = neo4j_session.run(
        """
        MATCH (rtab:EC2RouteTable)<-[:HAS_EXPLICIT_ROUTE_TABLE]-(snet:EC2Subnet)<-[:PART_OF_SUBNET]-(instance:EC2Instance) return instance.id, snet.subnetid, rtab.id
        """,
    )
    for n in nodes:
        print("nonde",n)
    actual_nodes = {
        (
            n['instance.id'],
            n['snet.subnetid'],
            n['rtab.id'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_route_tables_implicit_relationships(neo4j_session):
    data = tests.data.aws.ec2.route_tables.DESCRIBE_ROUTE_TABLES
    cartography.intel.aws.ec2.route_tables.load_route_tables(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )
    data = tests.data.aws.ec2.subnets.DESCRIBE_SUBNETS
    cartography.intel.aws.ec2.subnets.load_subnets(
        neo4j_session,
        data,
         "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instance_data(
        neo4j_session,
        data,
         "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('i-01', 'route_table-2')
    }

    nodes = neo4j_session.run(
        """
        MATCH (rtab:EC2RouteTable)<-[:HAS_IMPLICIT_ROUTE_TABLE]-(instance:EC2Instance) return instance.id, rtab.id
        """,
    )
    for n in nodes:
        print("node::",n)
    actual_nodes = {
        (
            n['instance.id'],
            n['rtab.id'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

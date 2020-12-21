import cartography.intel.aws.ec2
import tests.data.aws.ec2.network_interfaces


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


def test_load_network_interfaces(neo4j_session):
    data = tests.data.aws.ec2.network_interfaces.DESCRIBE_NETWORK_INTERFACES
    cartography.intel.aws.ec2.network_interfaces.load(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "eni-0e106a07c15ff7d14",
        "eni-0d9877f559c240362",
        "eni-04b4289e1be7634e4",
    }

    nodes = neo4j_session.run(
        """
        MATCH (ni:NetworkInterface) RETURN ni.id;
        """,
    )
    actual_nodes = {n['ni.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_ec2_private_ips(neo4j_session):
    data = tests.data.aws.ec2.network_interfaces.DESCRIBE_NETWORK_INTERFACES
    cartography.intel.aws.ec2.network_interfaces.load(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "eni-0e106a07c15ff7d14:10.0.4.180",
        "eni-0d9877f559c240362:10.0.4.96",
        "eni-04b4289e1be7634e4:10.0.4.5",
        "eni-04b4289e1be7634e4:10.0.4.12",
    }

    nodes = neo4j_session.run(
        """
        MATCH (ni:EC2PrivateIp) RETURN ni.id;
        """,
    )
    actual_nodes = {n['ni.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_network_interface_relationships(neo4j_session):
    data = tests.data.aws.ec2.network_interfaces.DESCRIBE_NETWORK_INTERFACES
    cartography.intel.aws.ec2.network_interfaces.load(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('eni-0e106a07c15ff7d14', 'eni-0e106a07c15ff7d14:10.0.4.180'),
        ('eni-0d9877f559c240362', 'eni-0d9877f559c240362:10.0.4.96'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.5'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.12'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:NetworkInterface)-[:PRIVATE_IP_ADDRESS]->(n2:EC2PrivateIp) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected_nodes


def test_network_interface_to_account(neo4j_session):
    neo4j_session.run('MERGE (:AWSAccount{id:{ACC_ID}})', ACC_ID=TEST_ACCOUNT_ID)

    data = tests.data.aws.ec2.network_interfaces.DESCRIBE_NETWORK_INTERFACES
    cartography.intel.aws.ec2.network_interfaces.load(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('eni-0e106a07c15ff7d14', TEST_ACCOUNT_ID),
        ('eni-0d9877f559c240362', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:NetworkInterface)<-[:RESOURCE]-(n2:AWSAccount) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected_nodes

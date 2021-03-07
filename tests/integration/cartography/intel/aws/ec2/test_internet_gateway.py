import cartography.intel.aws.ec2
import tests.data.aws.ec2.internet_gateway

TEST_ACCOUNT_ID = '012345678912'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_internet_gateways(neo4j_session):
    data = tests.data.aws.ec2.internet_gateway.DESCRIBE_GATEWAYS
    cartography.intel.aws.ec2.internet_gateways.load_internet_gateways(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "igw-1234XXX",
        "igw-7e3a7c18",
        "igw-f1c81494",
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AWSInternetGateway) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}

    assert actual_nodes == expected_nodes

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSInternetGateway)<-[:RESOURCE]-(n2:AWSAccount) RETURN n1.id;
        """,
    )
    actual = {n['n1.id'] for n in result}

    assert actual == expected_nodes

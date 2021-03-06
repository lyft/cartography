import cartography.intel.aws.ec2
import tests.data.aws.ec2.internet_gateway

TEST_ACCOUNT_ID = '012345678912'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_internet_gateways(neo4j_session):
    data = tests.data.aws.ec2.igw.internet_gateways
    cartography.intel.aws.ec2.igw.load_internet_gateways(
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

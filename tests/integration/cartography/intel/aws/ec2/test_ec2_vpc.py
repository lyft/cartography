import cartography.intel.aws.ec2
import tests.data.aws.ec2.vpc


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


def test_load_vpcs(neo4j_session):
    data = tests.data.aws.ec2.vpc.DESCRIBE_VPCS
    cartography.intel.aws.ec2.vpc.load_ec2_vpcs(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "vpc-0e9801d129EXAMPLE",
        "vpc-06e4ab6c6cEXAMPLE",
    }

    nodes = neo4j_session.run(
        """
        MATCH (v:AWSVpc) RETURN v.id;
        """,
    )
    actual_nodes = {n['v.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_vpcs_and_flow_logs(neo4j_session):
    data = tests.data.aws.ec2.vpc.DESCRIBE_VPCS
    cartography.intel.aws.ec2.vpc.load_ec2_vpcs(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.vpc.DESCRIBE_FLOW_LOGS
    cartography.intel.aws.ec2.vpc.load_ec2_flow_logs(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('vpc-0e9801d129EXAMPLE', 'fl-aabbccdd112233445'),
        ('vpc-0e9801d129EXAMPLE', 'fl-01234567890123456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (v:AWSVpc)<-[:MONITORS]-(f:FlowLog) RETURN v.id, f.id;
        """,
    )
    actual = {
        (r['v.id'], r['f.id']) for r in result
    }
    assert actual == expected_nodes

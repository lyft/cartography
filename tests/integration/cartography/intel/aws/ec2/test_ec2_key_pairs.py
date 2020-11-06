import cartography.intel.aws.ec2
import tests.data.aws.ec2.key_pairs


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_ec2_key_pairs(neo4j_session, *args):
    data = tests.data.aws.ec2.key_pairs.DESCRIBE_KEY_PAIRS['KeyPairs']
    cartography.intel.aws.ec2.key_pairs.load_ec2_key_pairs(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_1",
            "11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11",
        ),
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_2",
            "22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22",
        ),
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_3",
            "33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (k:EC2KeyPair) return k.arn, k.keyfingerprint
        """,
    )
    actual_nodes = {
        (
            n['k.arn'],
            n['k.keyfingerprint'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

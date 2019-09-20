from string import Template

import cartography.intel.aws.ec2
import tests.data.aws.ec2

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_ec2_key_pairs(neo4j_session, *args):
    data = tests.data.aws.ec2.DESCRIBE_KEY_PAIRS
    cartography.intel.aws.ec2.load_ec2_key_pairs(
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
        """
    )
    actual_nodes = {
        (
            n['k.arn'],
            n['k.keyfingerprint'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_ec2_tags(neo4j_session):
    # Add resources that can be tagged
    MERGE_TEMPLATE = Template("""
        MERGE (n:$label{$property: 'tagged-${type}'})
        ON CREATE SET n.firstseen = timestamp()
        SET n.lastupdated = {aws_update_tag}
        """)

    for type, mapping in cartography.intel.aws.ec2.TAG_RESOURCE_TYPE_MAPPINGS.items():
        insert_statement = MERGE_TEMPLATE.safe_substitute(
            type=type,
            label=mapping.get('label'),
            property=mapping.get('property'),
        )
        neo4j_session.run(insert_statement, aws_update_tag=TEST_UPDATE_TAG)

    # Add tags
    data = tests.data.aws.ec2.DESCRIBE_TAGS
    cartography.intel.aws.ec2.load_ec2_tags(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ('Environment', 'Test', 'EC2Subnet'),
        ('Importance', 'High', 'EC2SecurityGroup'),
        ('Name', 'Private', 'AWSVPC'),
        ('Name', 'bar', 'NetworkInterface'),
        ('Name', 'foo', 'EC2Instance'),
    }

    nodes = neo4j_session.run(
        """
        MATCH (t:Tag)-[r:TAGGED]->(n) return t.key, r.value, labels(n)[0] AS label
        """
    )
    actual_nodes = {
        (
            n['t.key'],
            n['r.value'],
            n['label'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

import cartography.intel.aws.resourcegroupstaggingapi
import cartography.intel.aws.ec2.load_ec2_instances
import tests.data.aws.resourcegroupstaggingapi
import tests.data.aws.ec2.instances


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session):
    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES
    cartography.intel.aws.ec2.load_ec2_instances(neo4j_session, data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)


def test_load_ec2_tags(neo4j_session):
    data = tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE
    resource_type = 'ec2:instance'
    cartography.intel.aws.resourcegroupstaggingapi.load_tags(
        neo4j_session,
        data,
        resource_type,
        TEST_REGION,
        TEST_UPDATE_TAG,
    )
    expected = {
        ('i-01', 'TestKey:TestValue'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:EC2Instance)-[:TAGGED]->(n2:AWSTag) RETURN n1.id, n2.id;
        """
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

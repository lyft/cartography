import cartography.intel.aws.ec2
import cartography.intel.aws.resourcegroupstaggingapi as rgta
import tests.data.aws.ec2.instances
import tests.data.aws.resourcegroupstaggingapi


TEST_ACCOUNT_ID = '1234'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session):
    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session, data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )


def test_transform_and_load_ec2_tags(neo4j_session):
    """
    Verify that (:EC2Instance)-[:TAGGED]->(:AWSTag) relationships work as expected.
    """
    _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session)
    resource_type = 'ec2:instance'
    rgta.transform_tags(tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE, resource_type)
    rgta.load_tags(
        neo4j_session,
        tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE,
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
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

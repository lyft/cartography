import copy

import cartography.intel.aws.ec2
import cartography.intel.aws.resourcegroupstaggingapi as rgta
import tests.data.aws.ec2.instances
import tests.data.aws.resourcegroupstaggingapi
from tests.integration.cartography.intel.aws.common import create_test_account


TEST_ACCOUNT_ID = '1234'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
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
    get_resources_response = copy.deepcopy(tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE)
    rgta.transform_tags(get_resources_response, resource_type)
    rgta.load_tags(
        neo4j_session,
        get_resources_response,
        resource_type,
        TEST_REGION,
        TEST_ACCOUNT_ID,
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

    # Test the cleanup removes old tags that are not attached to any resource
    new_update_tag = TEST_UPDATE_TAG + 1
    new_response = copy.deepcopy(tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE_UPDATED)
    rgta.transform_tags(new_response, resource_type)
    rgta.load_tags(
        neo4j_session,
        new_response,
        resource_type,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        new_update_tag,
    )
    neo4j_session.run('MATCH (i:EC2Instance) DETACH DELETE (i) RETURN COUNT(*) as TotalCompleted')
    rgta.cleanup(neo4j_session, {'AWS_ID': TEST_ACCOUNT_ID, 'UPDATE_TAG': new_update_tag})
    expected = {
        ('TestKeyUpdated:TestValueUpdated'),
    }
    result = neo4j_session.run('MATCH (t:AWSTag) RETURN t.id')
    print(result)
    actual = {
        (r['t.id']) for r in result
    }
    assert actual == expected

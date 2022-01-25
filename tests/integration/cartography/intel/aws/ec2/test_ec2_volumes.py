import cartography.intel.aws.ec2.instances
import cartography.intel.aws.ec2.volumes
import tests.data.aws.ec2.instances
import tests.data.aws.ec2.volumes

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_volumes(neo4j_session):
    # Arrange
    data = tests.data.aws.ec2.volumes.DESCRIBE_VOLUMES
    transformed_data = cartography.intel.aws.ec2.volumes.transform_volumes(data, TEST_REGION, TEST_ACCOUNT_ID)

    # Act
    cartography.intel.aws.ec2.volumes.load_volumes(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        "v-01", "v-02",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EBSVolume) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_volume_to_account_rels(neo4j_session):

    # Arrange: Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: {aws_account_id}})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = {aws_update_tag}
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Act: Load Test Volumes
    data = tests.data.aws.ec2.volumes.DESCRIBE_VOLUMES
    transformed_data = cartography.intel.aws.ec2.volumes.transform_volumes(data, TEST_REGION, TEST_ACCOUNT_ID)

    cartography.intel.aws.ec2.volumes.load_volumes(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected = {
        (TEST_ACCOUNT_ID, 'v-01'),
        (TEST_ACCOUNT_ID, 'v-02'),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EBSVolume) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_volume_to_instance_rels(neo4j_session):
    # Arrange: Load in ec2 instances first
    instance_data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session, instance_data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )
    # Prep the volume data
    raw_volumes = tests.data.aws.ec2.volumes.DESCRIBE_VOLUMES
    transformed_volumes = cartography.intel.aws.ec2.volumes.transform_volumes(raw_volumes, TEST_REGION, TEST_ACCOUNT_ID)

    # Act
    cartography.intel.aws.ec2.volumes.load_volume_relationships(
        neo4j_session,
        transformed_volumes,
        TEST_UPDATE_TAG,
    )

    # Assert
    result = neo4j_session.run(
        """
        MATCH (n1:EC2Instance)<-[:ATTACHED_TO_EC2_INSTANCE]-(n2:EBSVolume) RETURN n1.id, n2.id;
        """,
    )
    expected = {
        ('i-01', 'v-01'),
        ('i-02', 'v-02'),
    }
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected

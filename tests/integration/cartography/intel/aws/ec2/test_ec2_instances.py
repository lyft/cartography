import cartography.intel.aws.ec2
import cartography.intel.aws.iam
import tests.data.aws.ec2.instances
import tests.data.aws.iam

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_ec2_instances(neo4j_session, *args):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session, data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "i-01",
            "i-01",
        ),
        (
            "i-02",
            "i-02",
        ),
        (
            "i-03",
            "i-03",
        ),
        (
            "i-04",
            "i-04",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (i:EC2Instance) return i.id, i.instanceid
        """,
    )
    actual_nodes = {
        (
            n['i.id'],
            n['i.instanceid'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_ec2_reservations_to_instances(neo4j_session, *args):
    """
    Ensure that instances are connected to their expected reservations
    """
    data = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session, data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "r-01",
            "i-01",
        ),
        (
            "r-02",
            "i-02",
        ),
        (
            "r-03",
            "i-03",
        ),
        (
            "r-03",
            "i-04",
        ),
    }

    nodes = neo4j_session.run(
        """
    MATCH (r:EC2Reservation)<-[:MEMBER_OF_EC2_RESERVATION]-(i:EC2Instance) RETURN r.reservationid, i.id
    """,
    )
    actual_nodes = {
        (
            n['r.reservationid'],
            n['i.id'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_ec2_iaminstanceprofiles(neo4j_session):
    """
    Ensure that EC2Instances are attached to the IAM Roles that they can assume due to their IAM instance profiles
    """
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data_roles = tests.data.aws.iam.INSTANCE_PROFILE_ROLES['Roles']
    data_instance_profiles = tests.data.aws.iam.LIST_INSTANCE_PROFILES['InstanceProfiles']
    data_instances = tests.data.aws.ec2.instances.DESCRIBE_INSTANCES['Reservations']

    cartography.intel.aws.iam.load_roles(
        neo4j_session, data_roles, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )
    cartography.intel.aws.iam.load_instance_profiles(
        neo4j_session, data_instance_profiles, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.instances.load_ec2_instances(
        neo4j_session, data_instances, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )

    # Instance to profile
    expected_nodes = {
        ('arn:aws:iam::000000000000:instance-profile/PROFILE_NAME', 'i-01'),
        ('arn:aws:iam::000000000000:instance-profile/SERVICE_NAME_2', 'i-02'),
        ('arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME', 'i-03'),
        ('arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME', 'i-04'),
    }
    nodes = neo4j_session.run(
        """
        MATCH (i:EC2Instance)-[:HAS_INSTANCE_PROFILE]->(ip:InstanceProfile) return i.id, ip.arn
        """,
    )
    actual_nodes = {(n['ip.arn'], n['i.id']) for n in nodes}
    assert actual_nodes == expected_nodes

    # Profile to Role
    expected_nodes = {
        (
            'arn:aws:iam::000000000000:instance-profile/SERVICE_NAME_2',
            'arn:aws:iam::000000000000:role/SERVICE_NAME_2',
        ),
        (
            'arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME',
            'arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME',
        ),
    }
    nodes = neo4j_session.run(
        """
        MATCH (ip:InstanceProfile)-[:ASSOCIATED_WITH]->(r:AWSRole) return ip.arn, r.arn
        """,
    )
    actual_nodes = {(n['ip.arn'], n['r.arn']) for n in nodes}
    assert actual_nodes == expected_nodes

    # Instance to Role
    expected_nodes = {
        ('arn:aws:iam::000000000000:role/SERVICE_NAME_2', 'i-02'),
        ('arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME', 'i-03'),
        ('arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME', 'i-04'),
    }
    nodes = neo4j_session.run(
        """
        MATCH (i:EC2Instance)-[:STS_ASSUME_ROLE_ALLOW]->(r:AWSRole) return r.arn, i.id
        """,
    )
    actual_nodes = {(n['r.arn'], n['i.id']) for n in nodes}
    assert actual_nodes == expected_nodes

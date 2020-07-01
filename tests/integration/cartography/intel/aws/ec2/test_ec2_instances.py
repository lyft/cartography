import cartography.intel.aws.ec2
import tests.data.aws.ec2.instances

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

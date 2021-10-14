import cartography.intel.aws.ec2
import tests.data.aws.ec2.auto_scaling_groups


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_launch_configurations(neo4j_session, *args):
    data = tests.data.aws.ec2.auto_scaling_groups.GET_LAUNCH_CONFIGURATIONS
    cartography.intel.aws.ec2.auto_scaling_groups.load_launch_configurations(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        (
            "example",
            "arn:aws:autoscaling:us-east-1:000000000000:launchConfiguration:00000000-0000-0000-0000-000000000000:launchConfigurationName/example",  # noqa:E501
            "1632221734.0",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:LaunchConfiguration) return n.name, n.id, n.created_time
        """,
    )
    actual_nodes = {
        (
            n['n.name'],
            n['n.id'],
            n['n.created_time'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

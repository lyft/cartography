import cartography.intel.aws.ec2
import tests.data.aws.ec2.launch_templates


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_launch_templates(neo4j_session, *args):
    data = tests.data.aws.ec2.launch_templates.GET_LAUNCH_TEMPLATES
    cartography.intel.aws.ec2.launch_templates.load_launch_templates(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_templates = {
        (
            "lt-00000000000000000",
            "eks-00000000-0000-0000-0000-000000000000",
            "0000",
            1,
        ),
    }
    expected_versions = {
        (
            "lt-00000000000000000-1",
            "eks-00000000-0000-0000-0000-000000000000",
            1,
            "0000",
            "ami-00000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:LaunchTemplate)-[:VERSION]->(v:LaunchTemplateVersion)
        return n.id, n.name, n.create_time, n.latest_version_number, v.id, v.name,
               v.version_number, v.create_time, v.image_id
        """,
    )
    actual_templates = {
        (
            n['n.id'],
            n['n.name'],
            n['n.create_time'],
            n['n.latest_version_number'],
            n['v.id'],
        )
        for n in nodes
    }
    actual_versions = {
        (
            v['v.name'],
            v['v.version_number'],
            v['v.create_time'],
            v['v.image_id'],
        )
        for v in nodes
    }
    assert actual_templates == expected_templates
    assert actual_versions == expected_versions

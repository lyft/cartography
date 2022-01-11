import cartography.intel.aws.ecs
import tests.data.aws.ecs


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789
CLUSTER_ARN = 'arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster'


def test_load_ecs_clusters(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_CLUSTERS
    cartography.intel.aws.ecs.load_ecs_clusters(neo4j_session, data, TEST_REGION, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            CLUSTER_ARN,
            "test_cluster"
            "ACTIVE",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSCluster)
        RETURN n.id, n.name, n.status
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.name'],
            n['n.status'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_ecs_container_instances(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_CONTAINER_INSTANCES
    cartography.intel.aws.ecs.load_ecs_container_instances(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
            "i-00000000000000000",
            "ACTIVE",
            100000,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainerInstance)
        RETURN n.id, n.ec2_instance_id, n.status, n.version
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.ec2_instance_id'],
            n['n.status'],
            n['n.version'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_ecs_services(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_SERVICES
    cartography.intel.aws.ecs.load_ecs_services(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
            "test_service",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "ACTIVE",
            100000,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSService)
        RETURN n.id, n.name, n.cluster_arn, n.status, n.created_at
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.name'],
            n['n.cluster_arn'],
            n['n.status'],
            n['n.created_at'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_ecs_task_definitions(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_TASK_DEFINITIONS
    cartography.intel.aws.ecs.load_ecs_task_definitions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test:0",
            "test_service",
            "ACTIVE",
            4,
            40000,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSTaskDefinition)
        RETURN n.id, n.family, n.status, n.version, n.registered_at
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.family'],
            n['n.status'],
            n['n.version'],
            n['n.registered_at'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test:0-test",
            "test",
            "test/test:latest",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainerDefinition)
        RETURN n.id, n.name, n.image
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.name'],
            n['n.image'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


def test_load_ecs_tasks(neo4j_session, *args):
    data = tests.data.aws.ecs.GET_ECS_TASKS
    cartography.intel.aws.ecs.load_ecs_tasks(
        neo4j_session,
        CLUSTER_ARN,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
            "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
            "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
            "service:test_service",
            10000,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSTask)
        RETURN n.id, n.task_definition_arn, n.cluster_arn, n.group, n.created_at
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.task_definition_arn'],
            n['n.cluster_arn'],
            n['n.group'],
            n['n.created_at'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    expected_nodes = {
        (
            "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",  # noqa:E501
            "test-task_container",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:ECSContainer)
        RETURN n.id, n.name, n.image, n.image_digest
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            n['n.name'],
            n['n.image'],
            n['n.image_digest'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
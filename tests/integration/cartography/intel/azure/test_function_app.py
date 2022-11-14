from cartography.intel.azure import function_app
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPBACKUPS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPCONFIGURATIONS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPDEPLOYMENTS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPFUNCTIONS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPPROCESSES
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPSNAPSHOTS
from tests.data.azure.function_app import DESCRIBE_FUNCTIONAPPWEBJOBS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


def test_load_function_apps(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionApp) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureFunctionApp) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_configurations(neo4j_session):
    function_app.load_function_apps_configurations(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPCONFIGURATIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/config/Conf1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/config/Conf2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppConfiguration) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_configuration_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_configurations(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPCONFIGURATIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/config/Conf1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/config/Conf2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppConfiguration) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_functions(neo4j_session):
    function_app.load_function_apps_functions(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPFUNCTIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/functions/functon1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/functions/functon2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppFunction) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_function_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_functions(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPFUNCTIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/functions/functon1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/functions/functon2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppFunction) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_deployments(neo4j_session):
    function_app.load_function_apps_deployments(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPDEPLOYMENTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/deployments/deploy1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/deployments/deploy2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppDeployment) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_deployment_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_deployments(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPDEPLOYMENTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/deployments/deploy1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/deployments/deploy2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppDeployment) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_backups(neo4j_session):
    function_app.load_function_apps_backups(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPBACKUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/backups/backup1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/backups/backup2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppBackup) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_backup_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_backups(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPBACKUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/backups/backup1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/backups/backup2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppBackup) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_process(neo4j_session):
    function_app.load_function_apps_processes(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPPROCESSES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/processes/process1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/processes/process2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppProcess) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_process_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_processes(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPPROCESSES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/processes/process1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/processes/process2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppProcess) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_snapshots(neo4j_session):
    function_app.load_function_apps_snapshots(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPSNAPSHOTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/snapshots/snap1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/snapshots/snap2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppSnapshot) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_snapshot_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_snapshots(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPSNAPSHOTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/snapshots/snap1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/snapshots/snap2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppSnapshot) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_function_app_webjobs(neo4j_session):
    function_app.load_function_apps_webjobs(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPWEBJOBS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/webjobs/webjob1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/webjobs/webjob2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFunctionAppWebjob) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_function_app_webjob_relationships(neo4j_session):
    function_app.load_function_apps(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_FUNCTIONAPPS,
        TEST_UPDATE_TAG,
    )

    function_app.load_function_apps_webjobs(
        neo4j_session,
        DESCRIBE_FUNCTIONAPPWEBJOBS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/webjobs/webjob1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/webjobs/webjob2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureFunctionApp)-[:CONTAIN]->(n2:AzureFunctionAppWebjob) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected

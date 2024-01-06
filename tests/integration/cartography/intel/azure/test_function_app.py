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





from cartography.intel.azure import securitycenter
from tests.data.azure.security_center import DESCRIBE_CONTACTS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789

def test_load_security_contacts(neo4j_session):
    securitycenter.load_security_contacts(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTACTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/providers/Microsoft.Security/securityContact/contact1",
        "/subscriptions/00-00-00-00/providers/Microsoft.Security/securityContact/contact2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureSecurityContact) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_load_key_vaults_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: {subscription_id}})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = {update_tag}
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    securitycenter.load_security_contacts(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CONTACTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/providers/Microsoft.Security/securityContact/contact1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/providers/Microsoft.Security/securityContact/contact2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureSecurityContact) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected
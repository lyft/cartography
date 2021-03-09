from cartography.intel.azure import sql
from tests.data.azure.sql import DESCRIBE_AD_ADMINS
from tests.data.azure.sql import DESCRIBE_DATABASES
from tests.data.azure.sql import DESCRIBE_DNS_ALIASES
from tests.data.azure.sql import DESCRIBE_ELASTIC_POOLS
from tests.data.azure.sql import DESCRIBE_FAILOVER_GROUPS
from tests.data.azure.sql import DESCRIBE_RECOVERABLE_DATABASES
from tests.data.azure.sql import DESCRIBE_RESTORE_POINTS
from tests.data.azure.sql import DESCRIBE_RESTORABLE_DROPPED_DATABASES
from tests.data.azure.sql import DESCRIBE_REPLICATION_LINKS
from tests.data.azure.sql import DESCRIBE_SERVERS
from tests.data.azure.sql import DESCRIBE_THREAT_DETECTION_POLICY
from tests.data.azure.sql import DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789


def test_load_servers(neo4j_session):
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureServer) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_server_relationships(neo4j_session):
    # Create Test Azure Subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: {subscription_id}})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = {update_tag}
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureServer) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_server_dns_aliases(neo4j_session):
    sql._load_server_dns_aliases(
        neo4j_session,
        DESCRIBE_DNS_ALIASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/dnsAliases/dns-alias-1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/dnsAliases/dns-alias-2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureServerDNSAlias) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_server_dns_aliases_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_server_dns_aliases(
        neo4j_session,
        DESCRIBE_DNS_ALIASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/dnsAliases/dns-alias-1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/dnsAliases/dns-alias-2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:USED_BY]->(n2:AzureServerDNSAlias) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_server_ad_admins(neo4j_session):
    sql._load_server_ad_admins(
        neo4j_session,
        DESCRIBE_AD_ADMINS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/providers/Microsoft.Sql/administrators/ActiveDirectory1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/providers/Microsoft.Sql/administrators/ActiveDirectory2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureServerADAdministrator) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_server_ad_admins_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_server_ad_admins(
        neo4j_session,
        DESCRIBE_AD_ADMINS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/providers/Microsoft.Sql/administrators/ActiveDirectory1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/providers/Microsoft.Sql/administrators/ActiveDirectory2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:ADMINISTERED_BY]->(n2:AzureServerADAdministrator) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_recoverable_databases(neo4j_session):
    sql._load_recoverable_databases(
        neo4j_session,
        DESCRIBE_RECOVERABLE_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/recoverabledatabases/RD1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/recoverabledatabases/RD2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureRecoverableDatabase) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_recoverable_databases_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_recoverable_databases(
        neo4j_session,
        DESCRIBE_RECOVERABLE_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/recoverabledatabases/RD1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/recoverabledatabases/RD2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:RESOURCE]->(n2:AzureRecoverableDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_restorable_dropped_databases(neo4j_session):
    sql._load_restorable_dropped_databases(
        neo4j_session,
        DESCRIBE_RESTORABLE_DROPPED_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/restorableDroppedDatabases/RDD1,001",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/restorableDroppedDatabases/RDD2,002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureRestorableDroppedDatabase) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_restorable_dropped_databases_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_restorable_dropped_databases(
        neo4j_session,
        DESCRIBE_RESTORABLE_DROPPED_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/restorableDroppedDatabases/RDD1,001",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/restorableDroppedDatabases/RDD2,002",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:RESOURCE]->(n2:AzureRestorableDroppedDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_failover_groups(neo4j_session):
    sql._load_failover_groups(
        neo4j_session,
        DESCRIBE_FAILOVER_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/failoverGroups/FG1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/failoverGroups/FG1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureFailoverGroup) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_failover_groups_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_failover_groups(
        neo4j_session,
        DESCRIBE_FAILOVER_GROUPS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/failoverGroups/FG1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/failoverGroups/FG1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:RESOURCE]->(n2:AzureFailoverGroup) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_elastic_pools(neo4j_session):
    sql._load_elastic_pools(
        neo4j_session,
        DESCRIBE_ELASTIC_POOLS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/elasticPools/EP1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/elasticPools/EP2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureElasticPool) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_elastic_pools_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_elastic_pools(
        neo4j_session,
        DESCRIBE_ELASTIC_POOLS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/elasticPools/EP1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/elasticPools/EP2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:RESOURCE]->(n2:AzureElasticPool) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_databases(neo4j_session):
    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureDatabase) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_databases_relationships(neo4j_session):
    # Create Test Azure SQL Server
    sql.load_server_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SERVERS,
        TEST_UPDATE_TAG,
    )

    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureServer)-[:RESOURCE]->(n2:AzureDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_replication_links(neo4j_session):
    sql._load_replication_links(
        neo4j_session,
        DESCRIBE_REPLICATION_LINKS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/replicationLinks/RL1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/replicationLinks/RL1",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureReplicationLink) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_replication_links_relationships(neo4j_session):
    # Create Test Azure Database
    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    sql._load_replication_links(
        neo4j_session,
        DESCRIBE_REPLICATION_LINKS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/replicationLinks/RL1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/replicationLinks/RL1",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureDatabase)-[:CONTAINS]->(n2:AzureReplicationLink) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_db_threat_detection_policies(neo4j_session):
    sql._load_db_threat_detection_policies(
        neo4j_session,
        DESCRIBE_THREAT_DETECTION_POLICY,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/securityAlertPolicies/TDP1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/securityAlertPolicies/TDP2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureDatabaseThreatDetectionPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_db_threat_detection_policies_relationships(neo4j_session):
    # Create Test Azure Database
    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    sql._load_db_threat_detection_policies(
        neo4j_session,
        DESCRIBE_THREAT_DETECTION_POLICY,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/securityAlertPolicies/TDP1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/securityAlertPolicies/TDP2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureDatabase)-[:CONTAINS]->(n2:AzureDatabaseThreatDetectionPolicy) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_restore_points(neo4j_session):
    sql._load_restore_points(
        neo4j_session,
        DESCRIBE_RESTORE_POINTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/restorepoints/RP1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/restorepoints/RP2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureRestorePoint) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_restore_points_relationships(neo4j_session):
    # Create Test Azure Database
    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    sql._load_restore_points(
        neo4j_session,
        DESCRIBE_RESTORE_POINTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/restorepoints/RP1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/restorepoints/RP2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureDatabase)-[:CONTAINS]->(n2:AzureRestorePoint) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_transparent_data_encryptions(neo4j_session):
    sql._load_transparent_data_encryptions(
        neo4j_session,
        DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/transparentDataEncryption/TAE1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/transparentDataEncryption/TAE2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureTransparentDataEncryption) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_transparent_data_encryptions_relationships(neo4j_session):
    # Create Test Azure Database
    sql._load_databases(
        neo4j_session,
        DESCRIBE_DATABASES,
        TEST_UPDATE_TAG,
    )

    sql._load_transparent_data_encryptions(
        neo4j_session,
        DESCRIBE_TRANSPARENT_DATA_ENCRYPTIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1/databases/testdb1/transparentDataEncryption/TAE1",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2",
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2/databases/testdb2/transparentDataEncryption/TAE2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureDatabase)-[:CONTAINS]->(n2:AzureTransparentDataEncryption) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

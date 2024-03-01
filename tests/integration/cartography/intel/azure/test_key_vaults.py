from cartography.intel.azure import key_vaults
from cartography.util import run_analysis_job
from tests.data.azure.key_vaults import DESCRIBE_CERTIFICATES
from tests.data.azure.key_vaults import DESCRIBE_KEYS
from tests.data.azure.key_vaults import DESCRIBE_KEYVAULTS
from tests.data.azure.key_vaults import DESCRIBE_SECRETS

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'TestRG'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '1234'
TEST_TENANT_ID = '1234'


def test_load_key_vaults(neo4j_session):
    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault1",
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureKeyVault) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_key_vaults_relationships(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})<-[:RESOURCE]-(:AzureTenant{id: $AZURE_TENANT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        AZURE_TENANT_ID=TEST_TENANT_ID,
        WORKSPACE_ID=TEST_WORKSPACE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault1",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureKeyVault) RETURN n1.id, n2.id;
        """, )

    actual = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual == expected


def test_load_key_vault_keys(neo4j_session):
    key_vaults.load_key_vaults_keys(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {'/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2'}
    nodes = neo4j_session.run(
        """
        MATCH (r:AzureKeyVaultKey) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_key_vauly_key_relationship(neo4j_session):
    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    key_vaults.load_key_vaults_keys(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault1',
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2',
        ),
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2',
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2',
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureKeyVault)-[:HAS_KEY]->(n2:AzureKeyVaultKey) RETURN n1.id, n2.id;
        """, )

    actual_nodes = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual_nodes == expected_nodes


def test_load_key_vault_secrets(neo4j_session):
    key_vaults.load_key_vaults_secrets(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SECRETS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "https://vault1.vault.azure.net/secrets/secret1/abcdefg",
        "https://vault1.vault.azure.net/secrets/secret2/hijklm",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureKeyVaultSecret) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_key_vault_secrets_relationship(neo4j_session):
    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    key_vaults.load_key_vaults_secrets(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_SECRETS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault1", "https://vault1.vault.azure.net/secrets/secret1/abcdefg"),
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2", "https://vault1.vault.azure.net/secrets/secret2/hijklm"),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureKeyVault)-[:HAS_SECRET]->(n2:AzureKeyVaultSecret) RETURN n1.id, n2.id;
        """, )

    actual_nodes = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual_nodes == expected_nodes


def test_load_key_vault_certificates(neo4j_session):
    key_vaults.load_key_vaults_certificates(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CERTIFICATES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "https://vault1.vault.azure.net/certificates/selfSignedCert01/012abc",
        "https://vault1.vault.azure.net/certificates/selfSignedCert02/123ghj",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureKeyVaultCertificate) RETURN r.id;
        """, )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_key_vault_certificates_relationship(neo4j_session):
    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    key_vaults.load_key_vaults_certificates(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_CERTIFICATES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault1", "https://vault1.vault.azure.net/certificates/selfSignedCert01/012abc"),
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2", "https://vault1.vault.azure.net/certificates/selfSignedCert02/123ghj"),
    }

    result = neo4j_session.run(
        """
        MATCH (n1:AzureKeyVault)-[:HAS_CERTIFICATE]->(n2:AzureKeyVaultCertificate) RETURN n1.id, n2.id;
        """, )

    actual_nodes = {(r['n1.id'], r['n2.id']) for r in result}

    assert actual_nodes == expected_nodes


def test_key_vaults_public_exposure_analysis(neo4j_session):
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})<-[:RESOURCE]-(:AzureTenant{id: $AZURE_TENANT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        AZURE_TENANT_ID=TEST_TENANT_ID,
        WORKSPACE_ID=TEST_WORKSPACE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    key_vaults.load_key_vaults(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_KEYVAULTS,
        TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        "AZURE_TENANT_ID": TEST_TENANT_ID,
    }

    run_analysis_job(
        'azure_keyvault_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    expected_nodes = {
        (
            '/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/vault2',
            'default_network_access',
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureKeyVault{exposed_internet: true}) RETURN r.id, r.exposed_internet_type;
        """,
    )
    actual_nodes = {(n['r.id'], ",".join(n['r.exposed_internet_type'])) for n in nodes}

    assert actual_nodes == expected_nodes

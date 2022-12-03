import cartography.intel.gcp.cloudkms
import tests.data.gcp.cloudkms


TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_kms_locations(neo4j_session):
    data = tests.data.gcp.cloudkms.CLOUD_KMS_LOCATIONS
    cartography.intel.gcp.cloudkms.load_kms_locations(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "us-east1",
        "us-east4",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPLocation) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_kms_keyrings(neo4j_session):
    data = tests.data.gcp.cloudkms.CLOUD_KMS_KEYRINGS
    cartography.intel.gcp.cloudkms.load_kms_key_rings(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "keyring1",
        "keyring2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPKMSKeyRing) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def load_kms_crypto_keys(neo4j_session):
    data = tests.data.gcp.cloudkms.CLOUD_KMS_CRYPTO_KEYS
    cartography.intel.gcp.cloudkms.load_kms_crypto_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "cryptokey123",
        "cryptokey456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPKMSCryptoKey) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_kms_location_relationship(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load KMS Locations
    data = tests.data.gcp.cloudkms.CLOUD_KMS_LOCATIONS
    cartography.intel.gcp.cloudkms.load_kms_locations(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, 'us-east1'),
        (TEST_PROJECT_NUMBER, 'us-east4'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPLocation) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_kms_keyring_relationship(neo4j_session):
    # Load KMS Locations
    data = tests.data.gcp.cloudkms.CLOUD_KMS_LOCATIONS
    cartography.intel.gcp.cloudkms.load_kms_locations(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load KMS Keyrings
    data = tests.data.gcp.cloudkms.CLOUD_KMS_KEYRINGS
    cartography.intel.gcp.cloudkms.load_kms_key_rings(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('us-east1', 'keyring1'),
        ('us-east4', 'keyring2'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPLocation)-[:RESOURCE]->(n2:GCPKMSKeyRing) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_kms_crypto_key_relationship(neo4j_session):
    # Load KMS keyrings
    data = tests.data.gcp.cloudkms.CLOUD_KMS_KEYRINGS
    cartography.intel.gcp.cloudkms.load_kms_key_rings(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load KMS Crypto Keys
    data = tests.data.gcp.cloudkms.CLOUD_KMS_CRYPTO_KEYS
    cartography.intel.gcp.cloudkms.load_kms_crypto_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('keyring1', 'cryptokey123'),
        ('keyring2', 'cryptokey456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPKMSKeyRing)-[:RESOURCE]->(n2:GCPKMSCryptoKey) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

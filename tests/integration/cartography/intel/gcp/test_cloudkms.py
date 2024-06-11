import cartography.intel.gcp.cloudkms
import tests.data.gcp.cloudkms
from cartography.util import run_analysis_job

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789
TEST_REGION = 'us-east-1a'
TEST_KEYRING_ID = 'keyring1'

TEST_WORKSPACE_ID = '1223344'
TEST_UPDATE_TAG = 123456789

common_job_parameters = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "WORKSPACE_ID": '1223344',
    "GCP_PROJECT_ID": TEST_PROJECT_NUMBER,
}


def cloudanix_workspace_to_gcp_project(neo4j_session):
    query = """
    MERGE (w:CloudanixWorkspace{id: $WorkspaceId})
    MERGE (project:GCPProject{id: $ProjectId})
    MERGE (w)-[:OWNER]->(project)
    """
    nodes = neo4j_session.run(
        query,
        WorkspaceId=TEST_WORKSPACE_ID,
        ProjectId=TEST_PROJECT_NUMBER,
    )


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


def test_cloudkms_function(neo4j_session):
    cloudanix_workspace_to_gcp_project(neo4j_session)
    data = tests.data.gcp.cloudkms.CLOUD_KMS_LOCATIONS
    cartography.intel.gcp.cloudkms.load_kms_locations(neo4j_session, data, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    data = tests.data.gcp.cloudkms.CLOUD_KMS_KEYRINGS
    cartography.intel.gcp.cloudkms.load_kms_key_rings(neo4j_session, data, TEST_PROJECT_NUMBER, TEST_UPDATE_TAG)
    bindings_data = tests.data.gcp.cloudkms.FUNCTION_POLICY_BINDINGS

    cartography.intel.gcp.cloudkms.attach_keyring_to_binding(neo4j_session, TEST_KEYRING_ID, bindings_data, TEST_UPDATE_TAG)

    query1 = """
    MATCH (binding:GCPBinding)<-[a:ATTACHED_BINDING]-(keyring:GCPKMSKeyRing)<-[r:RESOURCE]-(location:GCPLocation)<-[:RESOURCE]-(:GCPProject{id: $GCP_PROJECT_ID})<-[:OWNER]-(:GCPOrganization{id:$GCP_ORGANIZATION_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID}) \nWHERE keyring.exposed_internet=true
    RETURN keyring.id,keyring.exposed_internet,keyring.exposed_internet_type
    """
    run_analysis_job('gcp_kms_keyring_analysis.json', neo4j_session, common_job_parameters)

    objects1 = neo4j_session.run(query1, GCP_PROJECT_ID=TEST_PROJECT_NUMBER, WORKSPACE_ID=TEST_WORKSPACE_ID)

    actual_nodes = {
        (
            o['keyring.id'],
            o['keyring.exposed_internet'],
            ",".join(o['keyring.exposed_internet_type']),

        ) for o in objects1

    }

    expected_nodes = {

        (
            'keyring1',
            True,
            'allUsers,allAuthenticatedUsers',
        ),

    }

    assert actual_nodes == expected_nodes

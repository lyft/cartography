import cartography.intel.gcp.iam
import tests.data.gcp.iam


TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_iam_roles(neo4j_session):
    data = tests.data.gcp.iam.IAM_ROLES
    cartography.intel.gcp.iam.load_iam_roles(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/roles/logging.viewer',
        'projects/project123/roles/compute.viewer',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPIAMRole) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_workloadidentitypools(neo4j_session):
    data = tests.data.gcp.iam.IAM_WORKLOADIDENTITYPOOLS
    cartography.intel.gcp.iam.load_workloadidentitypools(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG

    )

    expected_nodes = {
        'projects/000000000000/workloadIdentityPools/workloadidentitypool123',
        'projects/000000000000/workloadIdentityPools/workloadidentitypool456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPIAMWorkloadidentitypool) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_workloadidentitypoolsproviders(neo4j_session):
    data = tests.data.gcp.iam.IAM_WORKLOADIDENTITYPOOLPROVIDERS
    cartography.intel.gcp.iam.load_workloadidentitypools_providers(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG

    )

    expected_nodes = {
        'projects/000000000000/workloadIdentityPools/workloadidentitypool123/workloadIdentityPoolsProviders/provider123',
        'projects/000000000000/workloadIdentityPools/workloadidentitypool456/workloadIdentityPoolsProviders/provider456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPIAMWorloadidentitypoolprovider) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_service_accounts(neo4j_session):
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNTS
    cartography.intel.gcp.iam.load_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/serviceAccounts/abc@gmail.com',
        'projects/project123/serviceAccounts/defg@gmail.com',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPIAMServiceAccount) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_roles_relationships(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: {PROJECT_NUMBER}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load IAM Roles
    data = tests.data.gcp.iam.IAM_ROLES
    cartography.intel.gcp.iam.load_iam_roles(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    expected = {
        (TEST_PROJECT_NUMBER, "projects/project123/roles/logging.viewer"),
        (TEST_PROJECT_NUMBER, "projects/project123/roles/compute.viewer"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPIAMRole) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_workloadidentitypools_relationships(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: {PROJECT_NUMBER}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Workload Identity Pools
    data = tests.data.gcp.iam.IAM_WORKLOADIDENTITYPOOLS
    cartography.intel.gcp.iam.load_workloadidentitypools(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    expected = {
        (TEST_PROJECT_NUMBER, "projects/000000000000/workloadIdentityPools/workloadidentitypool123"),
        (TEST_PROJECT_NUMBER, "projects/000000000000/workloadIdentityPools/workloadidentitypool456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPIAMWorkloadidentitypool) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_workloadidentitypoolsproviders_relationships(neo4j_session):
    # Load Workload Identity Pools
    data = tests.data.gcp.iam.IAM_WORKLOADIDENTITYPOOLS
    cartography.intel.gcp.iam.load_workloadidentitypools(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    # Load Workload Identity Pools Providers
    data = tests.data.gcp.iam.IAM_WORKLOADIDENTITYPOOLPROVIDERS
    cartography.intel.gcp.iam.load_workloadidentitypools_providers(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG

    )

    expected = {
        ("projects/000000000000/workloadIdentityPools/workloadidentitypool123", "projects/000000000000/workloadIdentityPools/workloadidentitypool123/workloadIdentityPoolsProviders/provider123"),
        ("projects/000000000000/workloadIdentityPools/workloadidentitypool456", "projects/000000000000/workloadIdentityPools/workloadidentitypool456/workloadIdentityPoolsProviders/provider456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPIAMWorkloadidentitypool)-[:RESOURCE]->(n2:GCPIAMWorkloadidentitypoolproviders) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_service_accounts_relationships(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: {PROJECT_NUMBER}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load IAM Service Accounts
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNTS
    cartography.intel.gcp.iam.load_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG
    )

    expected = {
        (TEST_PROJECT_NUMBER, "projects/project123/serviceAccounts/abc@gmail.com"),
        (TEST_PROJECT_NUMBER, "projects/project123/serviceAccounts/defg@gmail.com"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPIAMServiceAccount) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

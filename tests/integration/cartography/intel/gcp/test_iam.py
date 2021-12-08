import cartography.intel.gcp.iam
import tests.data.gcp.iam


TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = 'customer123'


def test_load_iam_roles(neo4j_session):
    data = tests.data.gcp.iam.IAM_ROLES
    cartography.intel.gcp.iam.load_roles(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
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


def test_load_service_accounts(neo4j_session):
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNTS
    cartography.intel.gcp.iam.load_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
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


def test_load_service_account_keys(neo4j_session):
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNT_KEYS
    cartography.intel.gcp.iam.load_service_account_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'abc@gmail.com/key123',
        'abc@gmail.com/key456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPServiceAccountKey) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_iam_users(neo4j_session):
    data = tests.data.gcp.iam.IAM_USERS
    cartography.intel.gcp.iam.load_users(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'user123',
        'user456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPUser) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_groups(neo4j_session):
    data = tests.data.gcp.iam.IAM_GROUPS
    cartography.intel.gcp.iam.load_groups(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'group123',
        'group456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPGroup) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_domains(neo4j_session):
    data = tests.data.gcp.iam.IAM_DOMAINS
    cartography.intel.gcp.iam.load_domains(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'customers/customer123/domains/xyz.com',
        'customers/customer123/domains/pqr.com',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDomain) RETURN r.id;
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
    cartography.intel.gcp.iam.load_roles(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
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
        TEST_UPDATE_TAG,
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


def test_service_accounts_keys_relationships(neo4j_session):

    # Load IAM Service Accounts
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNTS
    cartography.intel.gcp.iam.load_service_accounts(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Service Account Keys
    data = tests.data.gcp.iam.IAM_SERVICE_ACCOUNT_KEYS
    cartography.intel.gcp.iam.load_service_account_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ("projects/project123/serviceAccounts/abc@gmail.com", 'abc@gmail.com/key123'),
        ("projects/project123/serviceAccounts/defg@gmail.com", 'defg@gmail.com/key456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPIAMServiceAccount)-[:RESOURCE]->(n2:GCPServiceAccountKey) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_users_relationships(neo4j_session):
    # Create Test GCPCustomer
    neo4j_session.run(
        """
        MERGE (gcp:GCPCustomer{id: {CUSTOMER_ID}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        CUSTOMER_ID=TEST_CUSTOMER_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load users
    data = tests.data.gcp.iam.IAM_USERS
    cartography.intel.gcp.iam.load_users(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('customer123', 'user123'),
        ('customer123', 'user456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPCustomer)-[:RESOURCE]->(n2:GCPUser) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_groups_relationships(neo4j_session):
    # Create Test GCPCustomer
    neo4j_session.run(
        """
        MERGE (gcp:GCPCustomer{id: {CUSTOMER_ID}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        CUSTOMER_ID=TEST_CUSTOMER_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Groups
    data = tests.data.gcp.iam.IAM_GROUPS
    cartography.intel.gcp.iam.load_groups(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('customer123', 'group123'),
        ('customer123', 'group456'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPCustomer)-[:RESOURCE]->(n2:GCPGroup) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_domains_relationships(neo4j_session):
    # Create Test GCPCustomer
    neo4j_session.run(
        """
        MERGE (gcp:GCPCustomer{id: {CUSTOMER_ID}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        CUSTOMER_ID=TEST_CUSTOMER_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Groups
    data = tests.data.gcp.iam.IAM_DOMAINS
    cartography.intel.gcp.iam.load_domains(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected = {
        ('customer123', 'customers/customer123/domains/xyz.com'),
        ('customer123', 'customers/customer123/domains/pqr.com'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPCustomer)-[:RESOURCE]->(n2:GCPDomain) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

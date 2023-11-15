import cartography.intel.gcp.cloudrun
import tests.data.gcp.cloudrun

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_cloudrun_authorized_domains(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_AUTHORIZED_DOMAINS
    cartography.intel.gcp.cloudrun.load_cloudrun_authorized_domains(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'example123.com',
        'example456.com',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunAuthorizedDomain) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cloudrun_configurations(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_CONFIGURATIONS
    cartography.intel.gcp.cloudrun.load_cloudrun_configurations(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'configuration123',
        'configuration456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunConfiguration) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cloudrun_domainmappings(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_DOMAIN_MAPPINGS
    cartography.intel.gcp.cloudrun.load_cloudrun_domainmappings(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'domainmap123',
        'domainmap456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunDomainMap) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cloudrun_revisions(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_REVISIONS
    cartography.intel.gcp.cloudrun.load_cloudrun_revisions(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'revision123',
        'revision456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunRevision) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cloudrun_routes(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_ROUTES
    cartography.intel.gcp.cloudrun.load_cloudrun_routes(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'route123',
        'route456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunRoute) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cloudrun_services(neo4j_session):
    data = tests.data.gcp.cloudrun.CLOUDRUN_SERVICES
    cartography.intel.gcp.cloudrun.load_cloudrun_services(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'service123',
        'service456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPCloudRunService) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_authorized_domains_relationships(neo4j_session):
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

    # Load Test Authorized Domains
    data = tests.data.gcp.cloudrun.CLOUDRUN_AUTHORIZED_DOMAINS
    cartography.intel.gcp.cloudrun.load_cloudrun_authorized_domains(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "example123.com"),
        (TEST_PROJECT_NUMBER, "example456.com"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunAuthorizedDomain) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_configurations_relationships(neo4j_session):
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

    # Load Test Configurations
    data = tests.data.gcp.cloudrun.CLOUDRUN_CONFIGURATIONS
    cartography.intel.gcp.cloudrun.load_cloudrun_configurations(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "configuration123"),
        (TEST_PROJECT_NUMBER, "configuration456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunConfiguration) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_domainmappings_relationships(neo4j_session):
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

    # Load Test Domain Mappings
    data = tests.data.gcp.cloudrun.CLOUDRUN_DOMAIN_MAPPINGS
    cartography.intel.gcp.cloudrun.load_cloudrun_domainmappings(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "domainmap123"),
        (TEST_PROJECT_NUMBER, "domainmap456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunDomainMap) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_revisions_relationships(neo4j_session):
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

    # Load Test Revisions
    data = tests.data.gcp.cloudrun.CLOUDRUN_REVISIONS
    cartography.intel.gcp.cloudrun.load_cloudrun_revisions(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "revision123"),
        (TEST_PROJECT_NUMBER, "revision456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunRevision) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_routes_relationships(neo4j_session):
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

    # Load Test Routes
    data = tests.data.gcp.cloudrun.CLOUDRUN_ROUTES
    cartography.intel.gcp.cloudrun.load_cloudrun_routes(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "route123"),
        (TEST_PROJECT_NUMBER, "route456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunRoute) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_services_relationships(neo4j_session):
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

    # Load Test Services
    data = tests.data.gcp.cloudrun.CLOUDRUN_SERVICES
    cartography.intel.gcp.cloudrun.load_cloudrun_services(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "service123"),
        (TEST_PROJECT_NUMBER, "service456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPCloudRunService) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

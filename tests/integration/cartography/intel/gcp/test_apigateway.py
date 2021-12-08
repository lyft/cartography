import cartography.intel.gcp.apigateway
import tests.data.gcp.apigateway

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_apigateway_locations(neo4j_session):
    data = tests.data.gcp.apigateway.TEST_APIGATEWAY_LOCATIONS
    cartography.intel.gcp.apigateway.load_apigateway_locations(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/locations/us-east1',
        'projects/project123/locations/us-east4',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPLocation) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_apigateway_api(neo4j_session):
    data = tests.data.gcp.apigateway.TEST_APIGATEWAY_APIS
    cartography.intel.gcp.apigateway.load_apis(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/locations/global/apis/compute',
        'projects/project123/locations/global/apis/storage',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPAPI) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_apigateway_apiconfig(neo4j_session):
    data = tests.data.gcp.apigateway.TEST_API_CONFIGS
    cartography.intel.gcp.apigateway.load_api_configs(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/locations/global/apis/compute/configs/config123',
        'projects/project123/locations/global/apis/compute/configs/config456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPAPIConfig) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_apigateway_gateway(neo4j_session):
    data = tests.data.gcp.apigateway.TEST_GATEWAYS
    cartography.intel.gcp.apigateway.load_gateways(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/locations/us-east1/gateways/gateway123',
        'projects/project123/locations/us-east1/gateways/gateway1456',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPAPIGateway) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_apigateway_location_relationships(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: {ProjectId}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create Test API Gateway Locations
    data = tests.data.gcp.apigateway.TEST_APIGATEWAY_LOCATIONS
    cartography.intel.gcp.apigateway.load_apigateway_locations(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_ID, 'projects/project123/locations/us-east1'),
        (TEST_PROJECT_ID, 'projects/project123/locations/us-east4'),
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


def test_apigateway_api_relationships(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: {ProjectID}})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = {UPDATE_TAG}
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create Test API Gateway APIs
    data = tests.data.gcp.apigateway.TEST_APIGATEWAY_APIS
    cartography.intel.gcp.apigateway.load_apis(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_ID, 'projects/project123/locations/global/apis/compute'),
        (TEST_PROJECT_ID, 'projects/project123/locations/global/apis/storage'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPAPI) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_apigateway_apiconfigs_relationships(neo4j_session):
    # Create Test API APIs
    data = tests.data.gcp.apigateway.TEST_APIGATEWAY_APIS
    cartography.intel.gcp.apigateway.load_apis(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create Test API Gateway API Configs
    data = tests.data.gcp.apigateway.TEST_API_CONFIGS
    cartography.intel.gcp.apigateway.load_api_configs(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected = {
        (
            'projects/project123/locations/global/apis/compute',
            'projects/project123/locations/global/apis/compute/configs/config123',
        ),
        (
            'projects/project123/locations/global/apis/storage',
            'projects/project123/locations/global/apis/compute/configs/config456',
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPAPI)-[:RESOURCE]->(n2:GCPAPIConfig) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_apigateway_gateway_relationships(neo4j_session):
    # Create Test API Gateway Configs
    data = tests.data.gcp.apigateway.TEST_API_CONFIGS
    cartography.intel.gcp.apigateway.load_api_configs(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create Test API Gateway Gateways
    data = tests.data.gcp.apigateway.TEST_GATEWAYS
    cartography.intel.gcp.apigateway.load_gateways(
        neo4j_session,
        data,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    expected = {
        (
            'projects/project123/locations/global/apis/compute/configs/config123',
            'projects/project123/locations/us-east1/gateways/gateway123',
        ),
        (
            'projects/project123/locations/global/apis/compute/configs/config456',
            'projects/project123/locations/us-east1/gateways/gateway456',
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPAPIConfig)-[:RESOURCE]->(n2:GCPAPIGateway) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

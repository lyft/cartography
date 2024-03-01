import cartography.intel.gcp.cloudcdn
import tests.data.gcp.cloudcdn

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789


def test_backend_buckets(neo4j_session):
    data = tests.data.gcp.cloudcdn.TEST_BACKEND_BUCKET
    cartography.intel.gcp.cloudcdn.load_backend_buckets(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/projects123/global/backendBuckets/backendbucket123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBackendBucket) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_global_backend_service(neo4j_session):
    data = tests.data.gcp.cloudcdn.TEST_GLOBAL_BACKEND_SERVICE
    cartography.intel.gcp.cloudcdn.load_backend_services(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/global/backendServices/globalser123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBackendService) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_regional_backend_service(neo4j_session):
    data = tests.data.gcp.cloudcdn.TEST_REGIONAL_BACKEND_SERVICE
    cartography.intel.gcp.cloudcdn.load_backend_services(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/regions/us-east1-a/backendServices/regionalser123', 'projects/project123/global/backendServices/globalser123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPBackendService) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_global_url_map(neo4j_session):
    data = tests.data.gcp.cloudcdn.TEST_GLOBAL_URL_MAP
    cartography.intel.gcp.cloudcdn.load_url_maps(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/global/urlmaps/globalmap123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPUrlMap) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_regional_url_map(neo4j_session):
    data = tests.data.gcp.cloudcdn.TEST_REGIONAL_URL_MAP

    cartography.intel.gcp.cloudcdn.load_url_maps(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        'projects/project123/regions/us-east1-a/urlmaps/regionalmap123', 'projects/project123/global/urlmaps/globalmap123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPUrlMap) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

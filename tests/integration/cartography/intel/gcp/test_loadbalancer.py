import cartography.intel.gcp.loadbalancer
import tests.data.gcp.loadbalancer

TEST_PROJECT_ID = 'project123'
TEST_UPDATE_TAG = 123456789

def test_global_health_check(neo4j_session):
    data = tests.data.gcp.loadbalancer.TEST_GLOBAL_HEALTH_CHECK
    cartography.intel.gcp.loadbalancer.load_health_checks(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/global/healthChecks/globalcheck123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPHealthCheck) WHERE r.type='global' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_regional_health_check(neo4j_session):
    data = tests.data.gcp.loadbalancer.TEST_REGIONAL_HEALTH_CHECK
    cartography.intel.gcp.loadbalancer.load_health_checks(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/regions/us-east1/healthChecks/regionalcheck123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPHealthCheck) WHERE r.type='regional' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_global_instance_group(neo4j_session):
    data = tests.data.gcp.loadbalancer.TEST_GLOBAL_INSTANCE_GROUP
    cartography.intel.gcp.loadbalancer.load_instance_groups(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/zones/us-east1-a/instanceGroups/globalgroup123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPInstanceGroup) WHERE r.type='global' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_regional_instance_group(neo4j_session):
    data = tests.data.gcp.loadbalancer.TEST_REGIONAL_INSTANCE_GROUP
    cartography.intel.gcp.loadbalancer.load_instance_groups(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/regions/us-east1/instanceGroups/regionalgroup123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPInstanceGroup) WHERE r.type='regional' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_global_url_map(neo4j_session):
    data =  tests.data.gcp.loadbalancer.TEST_GLOBAL_URL_MAP
    cartography.intel.gcp.loadbalancer.load_url_maps(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/global/urlmaps/globalmap123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPUrlMap) WHERE r.type='global' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_regional_url_map(neo4j_session):
    data =  tests.data.gcp.loadbalancer.TEST_REGIONAL_URL_MAP
    cartography.intel.gcp.loadbalancer.load_url_maps(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/regions/us-east1-a/urlmaps/regionalmap123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPUrlMap) WHERE r.type='regional' RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_ssl_policy(neo4j_session):
    data =  tests.data.gcp.loadbalancer.TEST_SSL_POLICY
    cartography.intel.gcp.loadbalancer.load_ssl_policies(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG
    )

    expected_nodes = {
        'projects/project123/global/urlmaps/sslpolicy123',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPSSLPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes
import cartography.intel.gcp.dns
import tests.data.gcp.dns

TEST_PROJECT_NUMBER = '000000000000'
TEST_UPDATE_TAG = 123456789


def test_load_dns_zones(neo4j_session):
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "111111111111111111111",
        "2222222222222222222",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDNSZone) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_rrs(neo4j_session):
    data = tests.data.gcp.dns.DNS_RRS
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "a.zone-1.example.com.",
        "b.zone-1.example.com.",
        "a.zone-2.example.com.",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPRecordSet) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_load_policies(neo4j_session):
    data = tests.data.gcp.dns.DNS_POLICIES
    cartography.intel.gcp.dns.load_dns_polices(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "projects/project123/policies/policy123",
        "projects/project123/policies/policy456",
        "projects/project123/policies/policy789",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDNSPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_load_keys(neo4j_session):
    data = tests.data.gcp.dns.DNS_KEYS
    cartography.intel.gcp.dns.load_dns_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "projects/project123/managedZones/zone123/dnsKeys/key123",
        "projects/project123/managedZones/zone456/dnsKeys/key456",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDNSKey) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes

def test_zones_relationships(neo4j_session):
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

    # Load Test DNS Zone
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "111111111111111111111"),
        (TEST_PROJECT_NUMBER, "2222222222222222222"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPDNSZone) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_rrs_relationships(neo4j_session):
    # Load Test DNS Zone
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Test RRS
    data = tests.data.gcp.dns.DNS_RRS
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ("111111111111111111111", "a.zone-1.example.com."),
        ("111111111111111111111", "b.zone-1.example.com."),
        ("2222222222222222222", "a.zone-2.example.com."),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPDNSZone)-[:HAS_RECORD]->(n2:GCPRecordSet) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

def test_policies_relationships(neo4j_session):
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

    # Load Test DNS Polices
    data = tests.data.gcp.dns.DNS_POLICIES
    cartography.intel.gcp.dns.load_dns_polices(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "projects/project123/policies/policy123"),
        (TEST_PROJECT_NUMBER, "projects/project123/policies/policy456"),
        (TEST_PROJECT_NUMBER, "projects/project123/policies/policy789"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPDNSPolicy) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected

def test_dns_keys_relationships(neo4j_session):
    # Load Test DNS Zone
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Test DNS Keys
    data = tests.data.gcp.dns.DNS_KEYS
    cartography.intel.gcp.dns.load_dns_keys(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ("111111111111111111111", "projects/project123/managedZones/zone123/dnsKeys/key123"),
        ("2222222222222222222", "projects/project123/managedZones/zone456/dnsKeys/key456"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPDNSZone)-[:HAS_KEY]->(n2:GCPDNSKey) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected
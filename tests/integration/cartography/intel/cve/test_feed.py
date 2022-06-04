import cartography.intel.cve.feed
import tests.data.cve.feed

TEST_UPDATE_TAG = 123456789


def test_load_cves(neo4j_session):
    cve_data = tests.data.cve.feed.GET_CVE_SYNC_METADATA
    cartography.intel.cve.feed.load_cves(neo4j_session, cve_data, TEST_UPDATE_TAG)

    expected_nodes = {
        (
            "CVE-1999-0001",
            tuple(["CWE-20"]),
            tuple(["http://www.openbsd.org/errata23.html#tcpfix", "http://www.osvdb.org/5707"]),
            (
                "ip_input.c in BSD-derived TCP/IP implementations allows remote attackers to cause a "
                "denial of service (crash or hang) via crafted packets."
            ),
        ),
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:CVE) RETURN n.id, n.problem_types, n.references, n.description_en
        """,
    )
    actual_nodes = {
        (
            n['n.id'],
            tuple(n['n.problem_types']),
            tuple(n['n.references']),
            n['n.description_en'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

from cartography.intel.kubernetes.ingresses import load_ingresses
from tests.data.kubernetes.ingresses import GET_INGRESSES_DATA
from tests.integration.cartography.intel.kubernetes.test_services import test_load_services


TEST_UPDATE_TAG = 123456789


def test_load_ingresses(neo4j_session):
    test_load_services(neo4j_session)
    load_ingresses(neo4j_session, GET_INGRESSES_DATA, TEST_UPDATE_TAG)

    results = list(
        neo4j_session.run(
            """
            MATCH
                (: KubernetesNamespace)-[:HAS_INGRESS]->
                (i: KubernetesIngress)-[:HAS_RULE]->
                (r: KubernetesIngressRule)-[:HAS_PATH]->
                (p: KubernetesIngressRuleHttpPath)-[:HAS_SERVICE]->
                (: KubernetesService)
            RETURN i.name, r.host, p.path
            """,
        ),
    )
    assert len(results) == 1
    result = results[0]
    assert result["i.name"] == "my-ingress"
    assert result["r.host"] == "my-host"
    assert result["p.path"] == "/admin"

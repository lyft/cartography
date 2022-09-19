import logging
from typing import Dict
from typing import List

from kubernetes.client.models.v1_ingress_list import V1IngressList
from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_ingresses(
    session: Session,
    client: K8sClient,
    update_tag: int,
    cluster: Dict,
) -> List[Dict]:
    ingresses = get_ingresses(client)
    ingresses_data = transform_ingresses(ingresses, cluster)
    load_ingresses(session, ingresses_data, update_tag)
    return ingresses


@timeit
def get_ingresses(client: K8sClient) -> V1IngressList:
    return client.networking.list_ingress_for_all_namespaces().items


@timeit
def transform_ingresses(ingresses: V1IngressList, cluster: Dict) -> List[Dict]:
    return [
        {
            "uid": ingress.metadata.uid,
            "name": ingress.metadata.name,
            "creation_timestamp": get_epoch(ingress.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(ingress.metadata.deletion_timestamp),
            "namespace": ingress.metadata.namespace,
            "cluster_uid": cluster["uid"],
            "labels": ingress.metadata.labels,
            "rules": [
                {
                    "host": r.host,
                    "http_paths": [
                        {
                            "path": p.path or "",
                            "path_type": p.path_type if p.path else "Empty",
                            "service": p.backend.service.name,
                            "port": p.backend.service.port.number,
                        }
                        for p in r.http.paths
                    ],
                }
                for r in ingress.spec.rules
            ],
            "tls": ingress.spec.tls,
        }
        for ingress in ingresses
    ]


def load_ingresses(session: Session, data: List[Dict], update_tag: int) -> None:
    ingestion_cypher_query = """
    UNWIND $ingresses as k8ingress
        MERGE (ingress:KubernetesIngress {id: k8ingress.uid})
        ON CREATE SET ingress.firstseen = timestamp()
        SET ingress.lastupdated = $update_tag,
            ingress.name = k8ingress.name,
            ingress.created_at = k8ingress.creation_timestamp,
            ingress.deleted_at = k8ingress.deletion_timestamp,
            ingress.tls = k8ingress.tls
        WITH ingress, k8ingress.namespace as ns, k8ingress.cluster_uid as cuid, k8ingress.rules as k8rules
        MATCH (cluster:KubernetesCluster {id: cuid})-[:HAS_NAMESPACE]->(space:KubernetesNamespace {name: ns})
        MERGE (space)-[rel1:HAS_INGRESS]->(ingress)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = $update_tag
        WITH space, ingress, k8rules
        UNWIND k8rules as k8rule
            MERGE (rule: KubernetesIngressRule {ingress_uid: ingress.id, host: k8rule.host})
            ON CREATE SET rule.firstseen = timestamp()
            SET rule.lastupdated = $update_tag
            WITH space, ingress, rule, k8rule.http_paths as k8httppaths
            MERGE (ingress) -[rel2:HAS_RULE]->(rule)
            ON CREATE SET rel2.firstseen = timestamp()
            SET rel2.lastupdated = $update_tag
            WITH space, ingress, rule, k8httppaths
            UNWIND k8httppaths as k8httppath
                MERGE (httppath: KubernetesIngressRuleHttpPath {
                    ingress_uid: ingress.id, host: rule.host, path: k8httppath.path, type: k8httppath.path_type
                })
                ON CREATE SET httppath.firstseen = timestamp()
                SET httppath.lastupdated = $update_tag,
                    httppath.port = k8httppath.port
                WITH space, rule, httppath, k8httppath.service as svcname
                MERGE (rule) -[rel3:HAS_PATH]->(httppath)
                ON CREATE SET rel3.firstseen = timestamp()
                SET rel3.lastupdated = $update_tag
                WITH space, httppath, svcname
                MATCH (space:KubernetesNamespace)-[:HAS_SERVICE]->(service: KubernetesService {name: svcname})
                MERGE (httppath)-[rel4:HAS_SERVICE]->(service)
                ON CREATE SET rel4.firstseen = timestamp()
                SET rel4.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} kubernetes ingresses.")
    session.run(ingestion_cypher_query, ingresses=data, update_tag=update_tag)

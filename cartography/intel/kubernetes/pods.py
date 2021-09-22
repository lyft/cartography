import logging
from typing import Dict
from typing import List

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_pods(
    session: Session, client: K8sClient, update_tag: int, cluster: Dict,
) -> List[Dict]:
    pods = list()
    for pod in client.core.list_pod_for_all_namespaces().items:
        pods.append(
            {
                "uid": pod.metadata.uid,
                "name": pod.metadata.name,
                "creation_timestamp": get_epoch(pod.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(pod.metadata.deletion_timestamp),
                "namespace": pod.metadata.namespace,
                "node": pod.spec.node_name,
                "cluster_uid": cluster["uid"],
                "labels": pod.metadata.labels,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                        "uid": f"{pod.metadata.uid}-{container.name}",
                    }
                    for container in pod.spec.containers
                ],
            },
        )
    load_pod_data(session, pods, update_tag)
    return pods


def load_pod_data(session: Session, data: List[Dict], update_tag: int) -> None:
    ingestion_cypher_query = """
    UNWIND {pods} as k8pod
        MERGE (pod:KubernetesPod {id: k8pod.uid})
        ON CREATE SET pod.firstseen = timestamp()
        SET pod.lastupdated = {update_tag},
            pod.name = k8pod.name,
            pod.created_at = k8pod.creation_timestamp,
            pod.deleted_at = k8pod.deletion_timestamp
        WITH pod, k8pod.namespace as ns, k8pod.cluster_uid as cuid, k8pod.containers as k8containers
        MATCH (space:KubernetesNamespace {name: ns})-[:IN_CLUSTER]->(cluster:KubernetesCluster {id: cuid})
        MERGE (space)-[rel1:HAS_POD]->(pod)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = {update_tag}
        WITH pod, space, cluster, k8containers
        MERGE (pod)-[rel2:IN_NAMESPACE]->(space)
        ON CREATE SET rel2.firstseen = timestamp()
        SET rel2.lastupdated = {update_tag}
        WITH pod, space, cluster, k8containers
        UNWIND k8containers as k8container
            MERGE (container: KubernetesContainer {id: k8container.uid})
            ON CREATE SET container.firstseen = timestamp()
            SET container.image = k8container.image,
                container.name = k8container.name,
                container.lastupdated = {update_tag}
            WITH pod, space, cluster, container
            MERGE (pod)-[rel3:HAS_CONTAINER]->(container)
            ON CREATE SET rel3.firstseen = timestamp()
            SET rel3.lastupdated = {update_tag}
            WITH pod, space, container
            MERGE (cluster)-[rel4:HAS_POD]->(pod)
            ON CREATE SET rel4.firstseen = timestamp()
            SET rel4.lastupdated = {update_tag}
            WITH space, container
            MERGE (container)-[rel5:IN_NAMESPACE]->(space)
            ON CREATE SET rel5.firstseen = timestamp()
            SET rel5.lastupdated = {update_tag}
    """
    logger.info(f"Loading {len(data)} kubernetes pods.")
    session.run(ingestion_cypher_query, pods=data, update_tag=update_tag)

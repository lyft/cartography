import logging
from typing import Dict
from typing import List

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8Client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_namespaces(session: Session, client: K8Client, update_tag: int) -> Dict:
    cluster = dict()
    namespaces = list()
    for namespace in client.core.list_namespace().items:
        namespaces.append(
            {
                "uid": namespace.metadata.uid,
                "name": namespace.metadata.name,
                "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(namespace.metadata.deletion_timestamp),
            },
        )
        if namespace.metadata.name == "kube-system":
            cluster = {"uid": namespace.metadata.uid, "name": client.name}
    load_namespace_data(session, namespaces, cluster, update_tag)
    return cluster


def load_namespace_data(
    session: Session, data: List[Dict], cluster: Dict, update_tag: int,
) -> None:
    ingestion_cypher_query = """
    MERGE (cluster:KubernetesCluster {id: {cluster_id}})
    ON CREATE SET cluster.firstseen = timestamp()
    SET cluster.name = {cluster_name},
        cluster.lastupdated = {update_tag}
    WITH cluster
    UNWIND {namespaces} as namespace
        MERGE (space:KubernetesNamespace {id: namespace.uid})
        ON CREATE SET space.firstseen = timestamp()
        SET space.lastupdated = {update_tag},
            space.name = namespace.name,
            space.created_at = namespace.creation_timestamp,
            space.deleted_at = namespace.deletion_timestamp
        WITH cluster, space
        MERGE (space)-[rel1:IN_CLUSTER]->(cluster)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = {update_tag}
        WITH space, cluster
        MERGE (cluster)-[rel2:HAS_NAMESPACE]->(space)
        ON CREATE SET rel2.firstseen = timestamp()
        SET rel2.lastupdated = {update_tag}
    """
    logger.info(f"Loading {len(data)} kubernetes namespaces.")
    session.run(
        ingestion_cypher_query,
        namespaces=data,
        cluster_id=cluster["uid"],
        cluster_name=cluster["name"],
        update_tag=update_tag,
    )

import logging
from typing import Dict
from typing import List

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_secrets(
    session: Session,
    client: K8sClient,
    update_tag: int,
    cluster: Dict,
) -> List[Dict]:
    secrets = get_secrets(client, cluster)
    load_secrets(session, secrets, update_tag)
    return secrets


@timeit
def get_secrets(client: K8sClient, cluster: Dict) -> List[Dict]:
    return [
        {
            "uid": secret.metadata.uid,
            "name": secret.metadata.name,
            "creation_timestamp": get_epoch(secret.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(secret.metadata.deletion_timestamp),
            "namespace": secret.metadata.namespace,
            "cluster_uid": cluster["uid"],
            "labels": secret.metadata.labels,
            "type": secret.type,
        }
        for secret in client.core.list_secret_for_all_namespaces().items
    ]


def load_secrets(session: Session, data: List[Dict], update_tag: int) -> None:
    ingestion_cypher_query = """
    UNWIND $secrets as k8secret
        MERGE (secret:KubernetesSecret {id: k8secret.uid})
        ON CREATE SET secret.firstseen = timestamp()
        SET secret.lastupdated = $update_tag,
            secret.name = k8secret.name,
            secret.created_at = k8secret.creation_timestamp,
            secret.deleted_at = k8secret.deletion_timestamp,
            secret.type = k8secret.type
        WITH secret, k8secret.namespace as ns, k8secret.cluster_uid as cuid
        MATCH (cluster:KubernetesCluster {id: cuid})-[:HAS_NAMESPACE]->(space:KubernetesNamespace {name: ns})
        MERGE (space)-[rel1:HAS_SECRET]->(secret)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} kubernetes secrets.")
    session.run(ingestion_cypher_query, secrets=data, update_tag=update_tag)

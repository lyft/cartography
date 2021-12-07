import logging

from neo4j import Session

from cartography.config import Config
from cartography.intel.kubernetes.namespaces import sync_namespaces
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.services import sync_services
from cartography.intel.kubernetes.util import get_k8s_clients
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_k8s_ingestion(session: Session, config: Config) -> None:

    common_job_parameters = {"UPDATE_TAG": config.update_tag}
    if not config.k8s_kubeconfig:
        logger.error("kubeconfig not found.")
        return

    for client in get_k8s_clients(config.k8s_kubeconfig):
        cluster = sync_namespaces(session, client, config.update_tag)
        pods = sync_pods(session, client, config.update_tag, cluster)
        sync_services(session, client, config.update_tag, cluster, pods)

    run_cleanup_job(
        "kubernetes_import_cleanup.json",
        session,
        common_job_parameters,
        package="cartography.data.jobs.cleanup",
    )

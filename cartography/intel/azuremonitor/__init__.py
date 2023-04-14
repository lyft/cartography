"""
cartography/intel/azuremonitor
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.azuremonitor.endpoints import sync_hosts
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_azuremonitor_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of Azure Monitor / Sentinel data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    # the real authentication is directly read from environment with usual Azure variables.
    if not (config.azuremonitor_workspace_name and config.azuremonitor_workspace_id):
        logger.error("azuremonitor config not found")
        return

    sync_hosts(
        neo4j_session,
        config.update_tag,
        (config.azuremonitor_workspace_name, config.azuremonitor_workspace_id),
    )
    run_cleanup_job(
        "azuremonitor_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.azuremonitor_workspace_name:
        group_id = config.azuremonitor_workspace_name
    merge_module_sync_metadata(
        neo4j_session,
        group_type="azuremonitor",
        group_id=group_id,
        synced_type="azuremonitor",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

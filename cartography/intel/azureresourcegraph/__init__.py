"""
cartography/intel/azureresourcegraph
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.azureresourcegraph.endpoints import sync_hosts
from cartography.intel.azureresourcegraph.util import get_authorization
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_azureresourcegraph_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of Azure Resource Graph data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if (
        not config.azureresourcegraph_client_id or
        not config.azureresourcegraph_client_secret
    ) and not config.azureresourcegraph_use_managedidentity:
        logger.error(
            "azureresourcegraph config not found and not requested managed identity.",
        )
        return

    authorization = get_authorization(
        config.azureresourcegraph_client_id,
        config.azureresourcegraph_client_secret,
        config.azureresourcegraph_tenant_id,
    )
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    run_cleanup_job(
        "azureresourcegraph_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.azureresourcegraph_tenant_id:
        group_id = config.azureresourcegraph_tenant_id
    merge_module_sync_metadata(
        neo4j_session,
        group_type="azureresourcegraph",
        group_id=group_id,
        synced_type="azureresourcegraph",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

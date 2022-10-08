"""
cartography/intel/mde
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.mde.endpoints import sync_hosts
from cartography.intel.mde.util import get_authorization

from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_mde_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of MDE data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.mde_client_id or not config.mde_client_secret:
        logger.error("mde config not found")
        return

    authorization = get_authorization(
        config.mde_client_id,
        config.mde_client_secret,
        config.mde_api_url,
        config.mde_tenant_id,
    )
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    run_cleanup_job(
        "mde_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.mde_api_url:
        group_id = config.mde_api_url
    merge_module_sync_metadata(
        neo4j_session,
        group_type="mde",
        group_id=group_id,
        synced_type="mde",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

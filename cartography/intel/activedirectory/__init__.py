"""
cartography/intel/activedirectory
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.activedirectory.endpoints import sync_hosts
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_activedirectory_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of ActiveDirectory data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.activedirectory_dirpath or not config.activedirectory_name:
        logger.error("activedirectory config not found")
        return

    authorization = config.activedirectory_dirpath
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    run_cleanup_job(
        "activedirectory_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.activedirectory_name:
        group_id = config.activedirectory_name
    merge_module_sync_metadata(
        neo4j_session,
        group_type="activedirectory",
        group_id=group_id,
        synced_type="activedirectory",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

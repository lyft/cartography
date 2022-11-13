"""
cartography/intel/sumologic
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.sumologic.endpoints import sync_hosts
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_sumologic_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of Sumologic data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.sumologic_access_id or not config.sumologic_access_key:
        logger.error("sumologic config not found")
        return

    authorization = (
        config.sumologic_access_id,
        config.sumologic_access_key,
        config.sumologic_api_url,
    )
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    run_cleanup_job(
        "sumologic_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.sumologic_api_url:
        group_id = config.sumologic_api_url
    merge_module_sync_metadata(
        neo4j_session,
        group_type="sumologic",
        group_id=group_id,
        synced_type="sumologic",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

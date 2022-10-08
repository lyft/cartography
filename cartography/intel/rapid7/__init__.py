"""
cartography/intel/rapid7
"""
import logging

import neo4j

from cartography.config import Config
from cartography.intel.rapid7.endpoints import sync_hosts
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_rapid7_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of Rapid7 data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if (
        not config.rapid7_user or
        not config.rapid7_password or
        not config.rapid7_server_url
    ):
        logger.error("rapid7 config not found")
        return

    authorization = (
        config.rapid7_user,
        config.rapid7_password,
        config.rapid7_server_url,
        config.rapid7_verify_cert,
    )
    # pylint: disable=too-many-function-args
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    run_cleanup_job(
        "rapid7_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if config.rapid7_server_url:
        group_id = config.rapid7_server_url
    merge_module_sync_metadata(
        neo4j_session,
        group_type="rapid7",
        group_id=group_id,
        synced_type="rapid7",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

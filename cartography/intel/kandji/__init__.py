import logging

import neo4j

from cartography.config import Config
from cartography.intel.kandji import devices
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_kandji_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    devices.sync(neo4j_session, config.kandji_base_uri, config.kandji_token, common_job_parameters)

    run_cleanup_job('kandji_import_devices_cleanup.json', neo4j_session, common_job_parameters)

    group_id = "public"
    if config.kandji_base_uri:
        group_id = config.kandji_base_uri

    merge_module_sync_metadata(
        neo4j_session,
        group_type='kandji',
        group_id=group_id,
        synced_type='kandji',
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

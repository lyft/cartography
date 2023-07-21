import logging

import neo4j

from cartography.config import Config
from cartography.intel.semgrep.findings import sync
from cartography.stats import get_stats_client
from cartography.util import timeit


logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_semgrep_ingestion(
    neo4j_session: neo4j.Session, config: Config,
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.semgrep_app_token:
        logger.info('Semgrep import is not configured - skipping this module. See docs to configure.')
        return
    if not config.github_config:
        logger.info('GitHub import is not configured - No relationship with GitHub repositories will be created.')
    sync(neo4j_session, config.semgrep_app_token, config.update_tag, common_job_parameters)

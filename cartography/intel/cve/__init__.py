import logging
from datetime import datetime

import neo4j

from cartography.config import Config
from cartography.intel.cve import feed
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_cve_ingestion(
    neo4j_session: neo4j.Session, config: Config,
) -> None:
    """
    Perform ingestion of CVE data from NIST APIs.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.cve_enabled:
        return

    # sync CVE year archives, if not yet synced
    existing_years = feed.get_cve_sync_metadata(neo4j_session)
    current_year = datetime.now().year
    for year in range(2002, current_year + 1):
        if year in existing_years:
            continue
        logger.info(f"Syncing CVE data for year {year}")
        cves = feed.get_cves(config.nist_cve_url, str(year))
        feed.load_cves(neo4j_session, cves, config.update_tag)
        merge_module_sync_metadata(
            neo4j_session,
            group_type='CVE',
            group_id=year,
            synced_type='year',
            update_tag=config.update_tag,
            stat_handler=stat_handler,
        )

    # sync modified data
    logger.info("Syncing CVE data for modified data")
    cves = feed.get_cves(config.nist_cve_url, 'modified')
    feed.load_cves(neo4j_session, cves, config.update_tag)
    merge_module_sync_metadata(
        neo4j_session,
        group_type='CVE',
        group_id=year,
        synced_type='modified',
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

    # sync recent data
    logger.info("Syncing CVE data for recent data")
    cves = feed.get_cves(config.nist_cve_url, 'recent')
    feed.load_cves(neo4j_session, cves, config.update_tag)
    merge_module_sync_metadata(
        neo4j_session,
        group_type='CVE',
        group_id=year,
        synced_type='recent',
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

    # CVEs are never deleted, so we don't need to run a cleanup job

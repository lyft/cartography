import logging

import neo4j

import cartography.intel.gandi.organization
import cartography.intel.gandi.zones
from cartography.config import Config
from cartography.intel.gandi.utils import GandiAPI
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_gandi_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Gandi data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.gandi_apikey:
        logger.info(
            'Gandi import is not configured - skipping this module. '
            'See docs to configure.',
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    api_session = GandiAPI(config.gandi_apikey)

    cartography.intel.gandi.organization.sync(
        neo4j_session,
        api_session,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.gandi.zones.sync(
        neo4j_session,
        api_session,
        config.update_tag,
        common_job_parameters,
    )

import logging

import neo4j
import requests

import cartography.intel.hibob.employees
from cartography.config import Config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_hibob_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of HiBob data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.hibob_api_key:
        logger.info('HiBob import is not configured - skipping this module. See docs to configure.')
        return

    session = requests.Session()
    session.headers.update({'Authorization': config.hibob_api_key})

    cartography.intel.hibob.employees.sync(neo4j_session, config.update_tag, session)

    run_cleanup_job(
        "hibob_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

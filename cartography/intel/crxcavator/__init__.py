import logging

import neo4j
from requests import exceptions

from cartography.config import Config
from cartography.intel.crxcavator.crxcavator import sync_extensions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_extension_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of CRXcavator data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.crxcavator_api_base_uri or not config.crxcavator_api_key:
        logger.warning('CRXcavator import is not configured - skipping this module. See docs to configure.')
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    # while we typically want to crash sync on failure of module,
    # the crxcavator API is still in beta and is not always available.
    # if we receive a requests exception from raise_for_status
    # we'll handle and continue with other modules, otherwise crash sync
    try:
        sync_extensions(
            neo4j_session, common_job_parameters, config.crxcavator_api_key,
            config.crxcavator_api_base_uri,
        )
        run_cleanup_job(
            'crxcavator_import_cleanup.json',
            neo4j_session,
            common_job_parameters,
        )
    except exceptions.RequestException as e:
        logger.error("Could not complete request to the CRXcavator API: {}", e)

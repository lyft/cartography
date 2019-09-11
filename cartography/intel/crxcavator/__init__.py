import logging
import os

from requests import exceptions

from cartography.intel.crxcavator.crxcavator import sync_extensions
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

# API key for CRXcavator generaated from crxcavator.io portal
CRXCAVATOR_API_KEY = os.environ.get('CREDENTIALS_CRXCAVATOR_API_KEY')

# API for the CRXcavator API - https://api.crxcavator.io/v1 as of 07/09/19
CRXCAVATOR_API_BASE_URL = os.environ.get('CRXCAVATOR_URL')


def start_extension_ingestion(neo4j_session, config):
    """
    If this module is configured, perform ingestion of CRXcavator data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not CRXCAVATOR_API_BASE_URL or not CRXCAVATOR_API_KEY:
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
        sync_extensions(neo4j_session, common_job_parameters, CRXCAVATOR_API_KEY, CRXCAVATOR_API_BASE_URL)
        run_cleanup_job(
            'crxcavator_import_cleanup.json',
            neo4j_session,
            common_job_parameters,
        )
    except exceptions.RequestException as e:
        logger.error("Could not complete request to the CRXcavator API: {}", e)

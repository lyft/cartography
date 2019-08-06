import logging
import os

from cartography.intel.crxcavator.crxcavator import sync_extensions
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

# API key for CRXcavator generaated from crxcavator.io portal
CRXCAVATOR_API_KEY = os.environ.get('CREDENTIALS_CRXCAVATOR_API_KEY')

# API for the CRXcavator API - https://api.crxcavator.io/v1 as of 07/09/19
CRXCAVATOR_API_BASE_URL = os.environ.get('CRXCAVATOR_URL')


def start_extension_ingestion(session, config):
    """
    If this module is configured, perform ingestion of CRXcavator data. Otherwise warn and exit
    :param session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not CRXCAVATOR_API_BASE_URL or not CRXCAVATOR_API_KEY:
        logger.warning('CRXcavator import is not configured - skipping this module. See docs to configure.')
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    sync_extensions(session, common_job_parameters, CRXCAVATOR_API_KEY, CRXCAVATOR_API_BASE_URL)
    run_cleanup_job(
        'crxcavator_import_cleanup.json',
        session,
        common_job_parameters,
    )

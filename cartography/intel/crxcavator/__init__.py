import logging
import os

from cartography.intel.crxcavator.crxcavator import sync_extensions
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

# API key for CRXcavator generaated from crxcavator.io portal
CRXcavator_API_KEY = os.environ.get('CREDENTIALS_CRXCAVATOR_API_KEY')

# API for the CRXcavator API - https://api.crxcavator.io/v1 as of 07/09/19
CRXcavator_API_BASE_URL = os.environ.get('CRXCAVATOR_URL')


def start_extension_ingestion(session, config):
    """
    If this module is configured, perform ingestion of CRXcavator data. Otherwise warn and exit
    :param session: Neo4J session for database interface
    :param config: Neo4J server URI and Update tag for data freshness
    :return: None
    """
    if not CRXcavator_API_BASE_URL or not CRXcavator_API_KEY:
        logger.warning('CRXcavator import is not configured - skipping this module')
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    sync_extensions(session, common_job_parameters, CRXcavator_API_KEY, CRXcavator_API_BASE_URL)
    run_cleanup_job(
        'crxcavator_import_cleanup.json',
        session,
        common_job_parameters
    )

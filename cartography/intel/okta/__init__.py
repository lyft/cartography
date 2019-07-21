import os
import logging

from cartography.intel.okta.oktaintel import start_okta_ingestion

logger = logging.getLogger(__name__)

OKTA_API_KEY = os.environ.get('CREDENTIALS_OKTA_API_KEY')

def start_okta_ingestion(session, config):
    """
    Starts the OKTA ingestion process
    :param session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """

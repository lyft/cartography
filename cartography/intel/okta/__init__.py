import logging

from cartography.intel.okta.oktaintel import sync


logger = logging.getLogger(__name__)


def start_okta_ingestion(session, config):
    """
    Starts the OKTA ingestion process
    :param session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    sync(session, config)

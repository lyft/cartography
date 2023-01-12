import logging

import neo4j
import requests

import cartography.intel.hexnode.device_groups
import cartography.intel.hexnode.devices
import cartography.intel.hexnode.policies
import cartography.intel.hexnode.users
from cartography.config import Config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_hexnode_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Hexnode data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    # TODO: Add doc
    # TODO: Add integration tests

    if not config.hexnode_tenant:
        logger.info('Hexnode import is not configured - skipping this module. See docs to configure.')
        return

    api_url = f"https://{config.hexnode_tenant}.hexnodemdm.com/api/v1"
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    api_session = requests.Session()
    api_session.headers.update({'Authorization': config.hexnode_api_key})

    cartography.intel.hexnode.users.sync(neo4j_session, config.update_tag, api_session, api_url)
    cartography.intel.hexnode.policies.sync(neo4j_session, config.update_tag, api_session, api_url)
    cartography.intel.hexnode.devices.sync(neo4j_session, config.update_tag, api_session, api_url)
    cartography.intel.hexnode.device_groups.sync(neo4j_session, config.update_tag, api_session, api_url)

    run_cleanup_job(
        "hexnode_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

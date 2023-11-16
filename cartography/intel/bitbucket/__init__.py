import base64
import json
import logging

import neo4j
from requests import exceptions

import cartography.intel.bitbucket.workspace
import cartography.intel.github.repos
import cartography.intel.github.teams
import cartography.intel.github.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_bitbucket_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of bitbucket  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.bitbucket_refresh_token:
        logger.info('bitbucket import is not configured - skipping this module. See docs to configure.')
        return

    refresh_token = config.bitbucket_refresh_token
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "UPDATE_TAG": config.update_tag,
    }

    try:
        cartography.intel.bitbucket.workspace.sync(
                neo4j_session,
                common_job_parameters,
                refresh_token
            )
            
            
    except exceptions.RequestException as e:
            logger.error("Could not complete request to the Bitbuket API: %s", e)
    return common_job_parameters
import base64
import json
import logging

from requests import exceptions

import cartography.intel.github.repos
import cartography.intel.github.users
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_github_ingestion(neo4j_session, config):
    """
    If this module is configured, perform ingestion of Github  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.github_config:
        logger.info('GitHub import is not configured - skipping this module. See docs to configure.')
        return

    auth_tokens = json.loads(base64.b64decode(config.github_config).decode())
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    # run sync for the provided github tokens
    for auth_data in auth_tokens['organization']:
        try:
            cartography.intel.github.users.sync(
                neo4j_session,
                common_job_parameters,
                auth_data['token'],
                auth_data['url'],
                auth_data['name'],
            )
            cartography.intel.github.repos.sync(
                neo4j_session,
                common_job_parameters,
                auth_data['token'],
                auth_data['url'],
                auth_data['name'],
            )
        except exceptions.RequestException as e:
            logger.error("Could not complete request to the GitHub API: %s", e)

import logging

import neo4j
import requests

from cartography.config import Config
from cartography.util import timeit
from cartography.intel.hibob.employees import sync_employees

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

    sync_employees(neo4j_session, config.update_tag, session)

    '''
    run_cleanup_job(
        "pagerduty_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type='pagerduty',
        group_id='module',
        synced_type="pagerduty",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )

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
    '''

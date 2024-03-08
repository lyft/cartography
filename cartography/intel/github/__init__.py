import base64
import json
import logging
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List

import neo4j
from neo4j import GraphDatabase
from requests import exceptions

from . import organization
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.graph.session import Session
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str, service_func: Any, config: Config, organization_name: str, url, refresh_token: str, common_job_parameters: Dict,
):
    logger.info(f"BEGIN processing for service: {service}")
    neo4j_auth = (config.neo4j_user, config.neo4j_password)
    neo4j_driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=neo4j_auth,
        max_connection_lifetime=config.neo4j_max_connection_lifetime,
    )
    service_func(
        Session(neo4j_driver), common_job_parameters, refresh_token, url, organization_name,
    )
    logger.info(f"END processing for service: {service}")


@timeit
def sync_organization(neo4j_session: neo4j.Session, config: Config, auth_data: Dict, common_job_parameters: Dict) -> None:
    try:
        logger.info("Syncing Github Organization: %s", common_job_parameters["ORGANIZATION_ID"])
        organization.sync(neo4j_session, auth_data["token"], auth_data["name"], auth_data["url"], common_job_parameters)

        requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())

        # Process each service in parallel.
        with ThreadPoolExecutor(max_workers=len(RESOURCE_FUNCTIONS)) as executor:
            futures = []
            for request in requested_syncs:
                if request in RESOURCE_FUNCTIONS:
                    futures.append(
                        executor.submit(
                            concurrent_execution,
                            request,
                            RESOURCE_FUNCTIONS[request],
                            config,
                            auth_data['name'],
                            auth_data['url'],
                            auth_data['token'],
                            common_job_parameters,

                        ),
                    )
                else:
                    raise ValueError(
                        f'Github sync function "{request}" was specified but does not exist. Did you misspell it?',
                    )

            for future in as_completed(futures):
                logger.info(f'Result from Future - Service Processing: {future.result()}')


    except exceptions.RequestException as e:
        logger.error("Could not complete request to the GitHub API: %s", e)


@timeit
def start_github_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
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
        sync_organization(neo4j_session, config, auth_data, common_job_parameters)

    return common_job_parameters

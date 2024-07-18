import logging
import os
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List

import neo4j
from neo4j import GraphDatabase
from requests import exceptions

import cartography.intel.gitlab.group
import cartography.intel.gitlab.members
import cartography.intel.gitlab.projects
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.graph.session import Session
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str, service_func: Any, config:Config,group_name:str, access_token:str,common_job_parameters: Dict,
):
    logger.info(f"BEGIN processing for service: {service}")
    neo4j_auth = (config.neo4j_user, config.neo4j_password)
    neo4j_driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=neo4j_auth,
        max_connection_lifetime=config.neo4j_max_connection_lifetime,
    )
    service_func(
        Session(neo4j_driver), group_name,access_token,
        common_job_parameters,
    )
    logger.info(f"END processing for service: {service}")

def _sync_one_gitlab_group(
    neo4j_session: neo4j.Session,
    group_name:str,
    access_token:str,
    common_job_parameters: Dict[str, Any],
    config:Config,
):
    logger.info(f"Syncing Gitlab Group: {common_job_parameters['GITLAB_GROUP_ID']} - {group_name}")

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())

    if os.environ.get("LOCAL_RUN","0") == "1":
        # BEGIN - Sequential Run

        sync_args = {
            'neo4j_session': neo4j_session,
            'common_job_parameters': common_job_parameters,
            'group_id': common_job_parameters['GITLAB_GROUP_ID'],
            'group_name': group_name,
            'access_token': access_token,
        }

        for func_name in requested_syncs:
            if func_name in RESOURCE_FUNCTIONS:
                logger.info(f"Processing {func_name}")
                RESOURCE_FUNCTIONS[func_name](**sync_args)

            else:
                raise ValueError(f'GITLAB sync function "{func_name}" was specified but does not exist. Did you misspell it?')

        # END - Sequential Run

    else:
        # BEGIN - Parallel Run

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
                            group_name,
                            access_token,
                            common_job_parameters,
                        ),
                    )
                else:
                    raise ValueError(
                        f'Gitlab sync function "{request}" was specified but does not exist. Did you misspell it?',
                    )

            for future in as_completed(futures):
                logger.info(f'Result from Future - Service Processing: {future.result()}')

        # END - Parallel Run

    return True

def _sync_multiple_groups(
    neo4j_session: neo4j.Session,
    access_token: str,
    groups:List[Dict],
    common_job_parameters: Dict[str, Any],
    config: Config,
) ->bool:
    for group in groups:
        if common_job_parameters["ACCOUNT_ID"].lower() != group.get('name').lower():
            continue

        common_job_parameters['GITLAB_GROUP_ID']=group.get('id')
        _sync_one_gitlab_group(neo4j_session,group.get('path'),access_token,common_job_parameters,config)
        run_cleanup_job('gitlab_group_cleanup.json', neo4j_session, common_job_parameters)

        del common_job_parameters['GITLAB_GROUP_ID']

    return True

@timeit
def start_gitlab_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of gitlab  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.gitlab_access_token:
        logger.info('gitlab import is not configured - skipping this module. See docs to configure.')
        return

    access_token = config.gitlab_access_token
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "ACCOUNT_ID": config.params['workspace']['account_id'],
        "UPDATE_TAG": config.update_tag,
    }

    try:
        groups_list =cartography.intel.gitlab.group.get_groups(access_token)

        cartography.intel.gitlab.group.sync(
            neo4j_session,
            groups_list,
            common_job_parameters,
        )

        _sync_multiple_groups(
            neo4j_session,
            access_token,
            groups_list,
            common_job_parameters,
            config,
        )

    except exceptions.RequestException as e:
            logger.error("Could not complete request to the Gitlab API: %s", e)

    return common_job_parameters

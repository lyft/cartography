import logging
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List

import neo4j
from neo4j import GraphDatabase
from requests import exceptions

import cartography.intel.bitbucket.members
import cartography.intel.bitbucket.projects
import cartography.intel.bitbucket.repositories
import cartography.intel.bitbucket.workspace
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.graph.session import Session
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str, service_func: Any, config:Config,workspace_name:str, access_token:str,common_job_parameters: Dict,
):
    logger.info(f"BEGIN processing for service: {service}")
    neo4j_auth = (config.neo4j_user, config.neo4j_password)
    neo4j_driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=neo4j_auth,
        max_connection_lifetime=config.neo4j_max_connection_lifetime,
    )
    service_func(
        Session(neo4j_driver), workspace_name,access_token,
        common_job_parameters,
    )
    logger.info(f"END processing for service: {service}")


def _sync_one_workspace(
    neo4j_session: neo4j.Session,
    workspace_name:str,
    access_token:str,
    common_job_parameters: Dict[str, Any],
    config:Config,
):
    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
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
                        workspace_name,
                        access_token,
                        common_job_parameters,

                    ),
                )
            else:
                raise ValueError(
                    f'Azure sync function "{request}" was specified but does not exist. Did you misspell it?',
                )

        for future in as_completed(futures):
            logger.info(f'Result from Future - Service Processing: {future.result()}')

    return True


def _sync_multiple_workspaces(
    neo4j_session: neo4j.Session,
    access_token: str,
    workspaces:List[Dict],
    common_job_parameters: Dict[str, Any],
    config: Config,
) ->bool:
    for workspace in workspaces:
        common_job_parameters['WORKSPACE_UUID']=workspace.get('uuid')
        _sync_one_workspace(neo4j_session,workspace.get('slug'),access_token,common_job_parameters,config)
        run_cleanup_job('bitbucket_workspace_cleanup.json', neo4j_session, common_job_parameters)

        del common_job_parameters['WORKSPACE_UUID']

    return True


@timeit
def start_bitbucket_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of bitbucket  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.bitbucket_access_token:
        logger.info('bitbucket import is not configured - skipping this module. See docs to configure.')
        return

    access_token = config.bitbucket_access_token
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "UPDATE_TAG": config.update_tag,
    }

    try:
        workspaces_list =cartography.intel.bitbucket.workspace.get_workspaces(access_token)

        cartography.intel.bitbucket.workspace.sync(
                neo4j_session,
                workspaces_list,
                common_job_parameters,
        )

        _sync_multiple_workspaces(
            neo4j_session,
            access_token,
            workspaces_list,
            common_job_parameters,
            config,
        )

    except exceptions.RequestException as e:
            logger.error("Could not complete request to the Bitbucket API: %s", e)

    return common_job_parameters

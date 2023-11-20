import logging
from typing import Any
from typing import Dict
from typing import List
import neo4j
from requests import exceptions
import cartography.intel.bitbucket.workspace
import cartography.intel.bitbucket.repositories
import cartography.intel.bitbucket.projects
import cartography.intel.bitbucket.members
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
        workspaces_list =cartography.intel.bitbucket.workspace.get_workspaces(refresh_token)
        
        cartography.intel.bitbucket.workspace.sync(
                neo4j_session,
                workspaces_list,
                common_job_parameters,
                
            )
        
        _sync_multiple_workspaces(
            neo4j_session,
            refresh_token,
            workspaces_list,
            common_job_parameters,
            )
        
            
            
    except exceptions.RequestException as e:
            logger.error("Could not complete request to the Bitbuket API: %s", e)
    return common_job_parameters


def _sync_multiple_workspaces(
    neo4j_session: neo4j.Session,
    refresh_token: str,
    workspaces:List[Dict],
    common_job_parameters: Dict[str, Any],
    ) ->bool:
    
    
    for workspace in workspaces:
        _sync_one_workspace(neo4j_session,workspace.get('name'),refresh_token,common_job_parameters)
        
    del common_job_parameters['WORKSPACE_UUID']
    return True

def _sync_one_workspace(
    neo4j_session: neo4j.Session,
    workspace_name:str,
    refresh_token:str,
    common_job_parameters: Dict[str, Any],
  ):
    cartography.intel.bitbucket.projects.sync(
                neo4j_session,
                workspace_name,
                refresh_token,
                common_job_parameters,     
            )
    cartography.intel.bitbucket.repositories.sync(
                neo4j_session,
                workspace_name,
                refresh_token,
                common_job_parameters,     
            )
    cartography.intel.bitbucket.members.sync(
                neo4j_session,
                workspace_name,
                refresh_token,
                common_job_parameters,     
            )
    
    return True
    
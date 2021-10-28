import logging
from typing import Dict
from typing import List

import neo4j

from azure.core.exceptions import HttpResponseError
from azure.mgmt.web import WebSiteManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def get_client(credentials: Credentials, subscription_id: str) -> WebSiteManagementClient:
    client = WebSiteManagementClient(credentials, subscription_id)
    return client

@timeit
def get_function_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        function_list = list(map(lambda x: x.as_dict(), client.web_apps.list()))

        for fun in function_list:
            x = fun['id'].split('/')
            fun['resource_group'] = x[x.index('resourceGroups') + 1]

        return function_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving functions - {e}")
        return []

def load_function(neo4j_session: neo4j.Session, subscription_id: str, function_list: List[Dict], update_tag: int) -> None:
    ingest_fun = """
    UNWIND {functions} AS function
    MERGE (f:AzureFunction{id: function.id})
    ON CREATE SET f.firstseen = timestamp(),
    f.type = function.type,
    f.location = function.location,
    f.resourcegroup = function.resource_group
    SET f.lastupdated = {update_tag}, 
    f.name = function.name, 
    f.container_size = function.container_size,
    f.default_host_name=function.default_host_name, 
    f.last_modified_time_utc=function.last_modified_time_utc,
    f.state=function.state, 
    f.repository_site_name=function.repository_site_name,
    f.daily_memory_time_quota=function.daily_memory_time_quota,
    f.availability_state=function.availability_state, 
    f.usage_state=function.usage_state
    WITH f
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(f)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_fun,
        functions=function_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )




def cleanup_function(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_function_cleanup.json', neo4j_session, common_job_parameters)


def sync_function(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    function_list = get_function_list(credentials, subscription_id)
    load_function(neo4j_session, subscription_id, function_list, update_tag)
    cleanup_function(neo4j_session, common_job_parameters)



@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing function for subscription '%s'.", subscription_id)

    sync_function(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)


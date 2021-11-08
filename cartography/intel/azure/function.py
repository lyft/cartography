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

def get_function_conf_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        function_list = get_function_list(credentials, subscription_id)
        function_conf_list=[]
        for function in function_list:
            function_conf_list.append(list(map(lambda x: x.as_dict(), client.web_apps.list_configurations(function['resource_group'],function['name'])))[0])
        
        for function in function_conf_list:
            x = function['id'].split('/')
            function['resource_group'] = x[x.index('resourceGroups') + 1] 
            function['function_id'] = function['id'][:function['id'].index("/config/web")]    
        return function_conf_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving functions configuration - {e}")
        return []


@timeit
def get_function_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        function_list = list(map(lambda x: x.as_dict(), client.web_apps.list()))

        for function in function_list:
            x = function['id'].split('/')
            function['resource_group'] = x[x.index('resourceGroups') + 1]

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

def load_function_conf(
        neo4j_session: neo4j.Session, function_conf_list: List[Dict], update_tag: int,
) -> None:
    ingest_function_conf = """
    UNWIND {function_conf_list} as function_conf
    MERGE (fc:AzureWebAppConfiguration{id: function_conf.id})
    ON CREATE SET fc.firstseen = timestamp(),
    fc.type = function_conf.type
    SET fc.name = function_conf.name,
    fc.lastupdated = {azure_update_tag},
    fc.resource_group_name=function_conf.resource_group,
    fc.number_of_workers=function_conf.number_of_workers,
    fc.net_framework_version=function_conf.net_framework_version,
    fc.php_version=function_conf.php_version,
    fc.python_version=function_conf.python_version, 
    fc.node_version=function_conf.node_version,
    fc.linux_fx_version=function_conf.linux_fx_version,
    fc.windows_fx_version=function_conf.windows_fx_version,
    fc.request_tracing_enabled=function_conf.request_tracing_enabled,
    fc.remote_debugging_enabled=function_conf.remote_debugging_enabled,
    fc.logs_directory_size_limit=function_conf.logs_directory_size_limit,
    fc.java_version=function_conf.java_version,
    fc.auto_heal_enabled=function_conf.auto_heal_enabled,
    fc.vnet_name=function_conf.vnet_name,
    fc.local_my_sql_enabled=function_conf.local_my_sql_enabled,
    fc.ftps_state=function_conf.ftps_state,
    fc.pre_warmed_instance_count=function_conf.pre_warmed_instance_count,
    fc.health_check_path=function_conf.health_check_path
    WITH fc, function_conf
    MATCH (s:AzureFunction{id: function_conf.function_id})
    MERGE (s)-[r:CONFIGURED_WITH]->(fc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_function_conf,
        function_conf_list=function_conf_list,
        azure_update_tag=update_tag,
    )

def cleanup_function_conf(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_function_conf_cleanup.json', neo4j_session, common_job_parameters)

def sync_function_conf(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    function_conf_list = get_function_conf_list(credentials, subscription_id)
    load_function_conf(neo4j_session, function_conf_list, update_tag)
    cleanup_function_conf(neo4j_session, common_job_parameters)

@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing function for subscription '%s'.", subscription_id)

    sync_function(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_function_conf(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)


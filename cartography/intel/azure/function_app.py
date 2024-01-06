import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.web import WebSiteManagementClient
from msrest.exceptions import DeserializationError
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import get_azure_resource_group_name
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_function_apps(
    session: neo4j.Session, subscription_id: str,
    data_list: List[Dict], update_tag: int,
) -> None:
    session.write_transaction(
        _load_function_apps_tx, subscription_id,
        data_list, update_tag,
    )

@timeit
def get_client(
    credentials: Credentials,
    subscription_id: str,
) -> WebSiteManagementClient:
    client = WebSiteManagementClient(credentials, subscription_id)
    return client


@timeit
def get_function_apps_list(client: WebSiteManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        function_app_list = list(
            map(lambda x: x.as_dict(), client.web_apps.list()),
        )
        function_list = []
        for function in function_app_list:
            function['resource_group'] = get_azure_resource_group_name(function.get('id'))
            function['hostNamesDisabled'] = function.get('properties', {}).get('host_names_disabled', True)
            function['location'] = function.get('location', '').replace(" ", "").lower()
            function['consolelink'] = azure_console_link.get_console_link(
                id=function['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                function_list.append(function)
            else:
                if function.get('location') in regions or function.get('location') == 'global':
                    function_list.append(function)
        return function_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving function apps - {e}")
        return []


def _load_function_apps_tx(
    tx: neo4j.Transaction, subscription_id: str,
    function_apps_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_function_apps = """
    UNWIND $function_apps_list AS function_app
    MERGE (f:AzureFunctionApp{id: function_app.id})
    ON CREATE SET f.firstseen = timestamp(),
    f.type = function_app.type,
    f.location = function_app.location,
    f.region = function_app.location,
    f.consolelink = function_app.consolelink,
    f.hostNamesDisabled = function_app.hostNamesDisabled,
    f.resourcegroup = function_app.resource_group
    SET f.lastupdated = $update_tag,
    f.name = function_app.name,
    f.container_size = function_app.container_size,
    f.default_host_name=function_app.default_host_name,
    f.last_modified_time_utc=function_app.last_modified_time_utc,
    f.state=function_app.state,
    f.repository_site_name=function_app.repository_site_name,
    f.daily_memory_time_quota=function_app.daily_memory_time_quota,
    f.availability_state=function_app.availability_state,
    f.usage_state=function_app.usage_state
    WITH f
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(f)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_function_apps,
        function_apps_list=function_apps_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for function_app in function_apps_list:
        resource_group = get_azure_resource_group_name(function_app.get('id'))
        _attach_resource_group_function_apps(tx,function_app['id'],resource_group,update_tag)
            
def _attach_resource_group_function_apps(tx: neo4j.Transaction,function_app_id: str,resource_group:str,update_tag: int) -> None:
    ingest_function_apps = """
    MATCH (f:AzureFunctionApp{id: $function_app_id})
    WITH f
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (f)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_function_apps,
        function_app_id=function_app_id,
        resource_group=resource_group,
        update_tag=update_tag
    )

def cleanup_function_apps(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        'azure_import_function_apps_cleanup.json', neo4j_session,
        common_job_parameters,
    )


def sync_function_apps(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list
) -> None:
    client = get_client(credentials, subscription_id)
    function_apps_list = get_function_apps_list(client, regions, common_job_parameters)

    load_function_apps(
        neo4j_session, subscription_id, function_apps_list,
        update_tag,
    )
    cleanup_function_apps(neo4j_session, common_job_parameters)
    
@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list
) -> None:
    logger.info(
        "Syncing function apps for subscription '%s'.",
        subscription_id,
    )

    sync_function_apps(
        neo4j_session, credentials, subscription_id, update_tag,
        common_job_parameters, regions
    )

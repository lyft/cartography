import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Any

from concurrent.futures import ThreadPoolExecutor, as_completed

import neo4j
from neo4j import GraphDatabase
from azure.core.exceptions import HttpResponseError
from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.resource import SubscriptionClient

from . import subscription
from . import tag
from . import tenant
from .resources import RESOURCE_FUNCTIONS
from .util.credentials import Authenticator
from .util.credentials import Credentials
from cartography.config import Config
from cartography.intel.azure.util.common import parse_and_validate_azure_requested_syncs
from cartography.util import timeit
from cartography.util import run_analysis_job

logger = logging.getLogger(__name__)


def concurrent_execution(
    service: str, service_func: Any, config: Config, credentials: Credentials, common_job_parameters: Dict, update_tag: int, subscription_id: str
):
    logger.info(f"BEGIN processing for service: {service}")

    regions = config.params.get('regions', None)

    neo4j_auth = (config.neo4j_user, config.neo4j_password)
    neo4j_driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=neo4j_auth,
        max_connection_lifetime=config.neo4j_max_connection_lifetime,
    )
    if service == 'iam':
        service_func(neo4j_driver.session(), credentials, credentials.tenant_id, update_tag, common_job_parameters)
    elif service == 'key_vaults':
        service_func(neo4j_driver.session(), credentials,
                     subscription_id, update_tag, common_job_parameters, regions)
    else:
        service_func(neo4j_driver.session(), credentials.arm_credentials,
                     subscription_id, update_tag, common_job_parameters, regions)
    logger.info(f"END processing for service: {service}")


def _sync_one_subscription(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    tenant: Dict,
    requested_syncs: List[str],
    update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:

    common_job_parameters['Azure_Primary_AD_Domain_Name'] = tenant['defaultDomain']

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
                        credentials,
                        common_job_parameters,
                        update_tag,
                        subscription_id
                    )
                )
            else:
                raise ValueError(
                    f'Azure sync function "{request}" was specified but does not exist. Did you misspell it?')

        for future in as_completed(futures):
            logger.info(f'Result from Future - Service Processing: {future.result()}')

    # call tag.sync() at the last, don't change position of tag.sync()
    tag.sync(neo4j_session, credentials.arm_credentials, subscription_id, update_tag, common_job_parameters, config)


def _sync_tenant(
    neo4j_session: neo4j.Session,
    tenant_obj: Dict,
    current_user: Optional[str],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure Tenant: %s", tenant_obj['tenantId'])
    tenant.sync(
        neo4j_session, tenant_obj, current_user, update_tag,
        common_job_parameters,
    )


def _sync_multiple_subscriptions(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    tenant_obj: Dict,
    subscriptions: List[Dict],
    requested_syncs: List[str],
    update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:
    logger.info("Syncing Azure subscriptions")

    tenant_id = tenant_obj['tenantId']

    subscription.sync(
        neo4j_session, tenant_id, subscriptions, update_tag,
        common_job_parameters,
    )

    common_job_parameters['AZURE_TENANT_ID'] = tenant_id

    for sub in subscriptions:
        logger.info(
            "Syncing Azure Subscription with ID '%s'",
            sub['subscriptionId'],
        )
        common_job_parameters['AZURE_SUBSCRIPTION_ID'] = sub['subscriptionId']

        _sync_one_subscription(
            neo4j_session,
            credentials,
            sub['subscriptionId'],
            tenant_obj,
            requested_syncs,
            update_tag,
            common_job_parameters,
            config,
        )

        run_analysis_job(
            'azure_vm_public_facing_asset_exposure.json',
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            'azure_network_public_facing_asset_exposure.json',
            neo4j_session,
            common_job_parameters,
        )

        del common_job_parameters["AZURE_SUBSCRIPTION_ID"]


@timeit
def start_azure_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    common_job_parameters = {
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
        "pagination": {},
    }

    try:
        # if config.azure_sp_auth:
        #     credentials = Authenticator().authenticate_sp(
        #         config.azure_tenant_id,
        #         config.azure_client_id,
        #         config.azure_client_secret,
        #     )
        # else:
        #     credentials = Authenticator().authenticate_cli()

        credentials = Authenticator().impersonate_user(
            config.azure_client_id,
            config.azure_client_secret,
            config.azure_redirect_uri,
            config.azure_refresh_token,
            config.azure_graph_scope,
            config.azure_azure_scope,
            config.azure_vault_scope,
            config.azure_subscription_id,
        )

    except Exception as e:
        logger.error(f"Unable to authenticate with Azure Service Principal, an error occurred: {e}. Make sure your Azure Service Principal details are provided correctly.", exc_info=True, stack_info=True)
        return

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.azure_requested_syncs:
        azure_requested_syncs_string = ""
        for service in config.azure_requested_syncs:
            azure_requested_syncs_string += f"{service.get('name', '')},"
            if service.get('pagination', None):
                pagination = service.get('pagination', {})
                pagination['hasNextPage'] = False
                common_job_parameters['pagination'][service.get('name', None)] = pagination
        requested_syncs = parse_and_validate_azure_requested_syncs(azure_requested_syncs_string[:-1])

    tenant_obj = tenant.get_active_tenant(credentials)
    common_job_parameters['Azure_Primary_AD_Domain_Name'] = tenant_obj['defaultDomain']

    _sync_tenant(
        neo4j_session,
        tenant_obj,
        credentials.get_current_user(),
        config.update_tag,
        common_job_parameters,
    )

    if config.azure_sync_all_subscriptions:
        subscriptions = subscription.get_all_azure_subscriptions(credentials, common_job_parameters)

    else:
        subscriptions = subscription.get_current_azure_subscription(
            credentials, credentials.subscription_id, common_job_parameters,
        )

    if not subscriptions:
        logger.warning(
            "No valid Azure credentials are found. No Azure subscriptions can be synced. Exiting Azure sync stage.",
        )
        return

    _sync_multiple_subscriptions(
        neo4j_session,
        credentials,
        tenant_obj,
        subscriptions,
        requested_syncs,
        config.update_tag,
        common_job_parameters,
        config,
    )
    del common_job_parameters['Azure_Primary_AD_Domain_Name']
    return common_job_parameters

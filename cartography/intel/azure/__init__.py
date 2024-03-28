import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from . import subscription
from . import tenant
from .resources import RESOURCE_FUNCTIONS
from .util.credentials import Authenticator
from .util.credentials import Credentials
from cartography.config import Config
from cartography.intel.azure.util.common import parse_and_validate_azure_requested_syncs
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _sync_one_subscription(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, requested_syncs: List[str],
) -> None:
    for request in requested_syncs:
        if request in RESOURCE_FUNCTIONS:
            RESOURCE_FUNCTIONS[request](
                neo4j_session, credentials.arm_credentials,
                subscription_id, update_tag, common_job_parameters,
            )
        else:
            raise ValueError(f'Azure sync function "{request}" was specified but does not exist. Did you misspell it?')


def _sync_tenant(
    neo4j_session: neo4j.Session, tenant_id: str, current_user: Optional[str], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure Tenant: %s", tenant_id)
    tenant.sync(neo4j_session, tenant_id, current_user, update_tag, common_job_parameters)  # type: ignore


def _sync_multiple_subscriptions(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, subscriptions: List[Dict],
    update_tag: int, common_job_parameters: Dict,
    requested_syncs: List[str],
) -> None:
    logger.info("Syncing Azure subscriptions")

    subscription.sync(neo4j_session, tenant_id, subscriptions, update_tag, common_job_parameters)

    for sub in subscriptions:
        logger.info("Syncing Azure Subscription with ID '%s'", sub['subscriptionId'])
        common_job_parameters['AZURE_SUBSCRIPTION_ID'] = sub['subscriptionId']

        _sync_one_subscription(
            neo4j_session, credentials,
            sub['subscriptionId'], update_tag, common_job_parameters, requested_syncs,
        )

    del common_job_parameters["AZURE_SUBSCRIPTION_ID"]


@timeit
def start_azure_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
    }

    try:
        if config.azure_sp_auth:
            credentials = Authenticator().authenticate_sp(
                config.azure_tenant_id, config.azure_client_id, config.azure_client_secret,
            )
        else:
            credentials = Authenticator().authenticate_cli()

    except Exception as e:
        logger.error(
            (
                "Unable to authenticate with Azure Service Principal, an error occurred: %s."
                "Make sure your Azure Service Principal details are provided correctly."
            ),
            e,
        )
        return

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.azure_requested_syncs:
        requested_syncs = parse_and_validate_azure_requested_syncs(config.azure_requested_syncs)

    _sync_tenant(
        neo4j_session, credentials.get_tenant_id(), credentials.get_current_user(), config.update_tag,
        common_job_parameters,
    )

    if config.azure_sync_all_subscriptions:
        subscriptions = subscription.get_all_azure_subscriptions(credentials)

    else:
        subscriptions = subscription.get_current_azure_subscription(credentials, credentials.subscription_id)

    if not subscriptions:
        logger.warning(
            "No valid Azure credentials are found. No Azure subscriptions can be synced. Exiting Azure sync stage.",
        )
        return

    _sync_multiple_subscriptions(
        neo4j_session, credentials, credentials.get_tenant_id(), subscriptions, config.update_tag,
        common_job_parameters, requested_syncs,
    )

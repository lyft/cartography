import logging

from cartography.intel.azure.credentials import Authenticator

from . import tenant
from . import subscription
from . import compute
from . import cosmosdb
from . import storage
from . import sql
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _sync_one_subscription(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    # compute.sync(neo4j_session, credentials.arm_credentials, subscription_id, sync_tag, common_job_parameters)
    cosmosdb.sync(neo4j_session, credentials.arm_credentials, subscription_id, sync_tag, common_job_parameters)
    storage.sync(neo4j_session, credentials.arm_credentials, subscription_id, sync_tag, common_job_parameters)
    sql.sync(neo4j_session, credentials.arm_credentials, subscription_id, sync_tag, common_job_parameters)


def _sync_tenant(neo4j_session, tenant_id, current_user, sync_tag, common_job_parameters):
    logger.debug("Syncing Azure Tenant: %s", tenant_id)
    tenant.sync(neo4j_session, tenant_id, current_user, sync_tag, common_job_parameters)


def _sync_multiple_subscriptions(neo4j_session, credentials, tenant_id, subscriptions, sync_tag, common_job_parameters):
    logger.debug("Syncing Azure subscriptions")

    subscription.sync(neo4j_session, tenant_id, subscriptions, sync_tag, common_job_parameters)

    for sub in subscriptions:
        logger.info("Syncing Azure Subscription with ID '%s'", sub['subscriptionId'])

        _sync_one_subscription(neo4j_session, credentials, sub['subscriptionId'], sync_tag, common_job_parameters)


@timeit
def start_azure_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
    }

    try:
        if config.azure_sp_auth:
            credentials = Authenticator().authenticate_sp(config.tenant_id, config.client_id, config.client_secret)
        else:
            credentials = Authenticator().authenticate_cli()
    except Exception as e:
        logger.debug("Error occurred calling Authenticator.authenticate().", exc_info=True)
        logger.error(
            (
                "Unable to authenticate with Azure Service Principal, an error occurred: %s. Make sure your Azure Service Principal details "
                "are provided correctly."
            ),
            e,
        )
        return

    _sync_tenant(neo4j_session, credentials.get_tenant_id(), credentials.get_current_user(), config.update_tag, common_job_parameters)

    if config.azure_sync_all_subscriptions:
        subscriptions = subscription.get_all_azure_subscriptions(credentials)

    else:
        subscriptions = subscription.get_current_azure_subscription(credentials, credentials.subscription_id)

    if not subscriptions:
        logger.warning(
            "No valid Azure credentials could be found. No Azure subscriptions can be synced. Exiting Azure sync stage.",
        )
        return

    _sync_multiple_subscriptions(neo4j_session, credentials, credentials.get_tenant_id(), subscriptions, config.update_tag, common_job_parameters)

    # run_analysis_job(
    #     'aws_ec2_asset_exposure.json',
    #     neo4j_session,
    #     common_job_parameters,
    # )

    # run_analysis_job(
    #     'aws_ec2_keypair_analysis.json',
    #     neo4j_session,
    #     common_job_parameters,
    # )

    # run_analysis_job(
    #     'aws_eks_asset_exposure.json',
    #     neo4j_session,
    #     common_job_parameters,
    # )

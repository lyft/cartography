import logging
from azure.mgmt.compute import ComputeManagementClient
from azure.common.credentials import ServicePrincipalCredentials, UserPassCredentials, get_azure_cli_credentials
from msrestazure.azure_active_directory import MSIAuthentication
from msrestazure.azure_active_directory import AADTokenCredentials
import adal

from . import compute
from . import vm
from . import tenant
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

AUTHORITY_HOST_URI = 'https://login.microsoftonline.com'
AZURE_CLI_CLIENT_ID = ''


def _sync_one_subscription(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    compute.sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)


# def _autodiscover_accounts(neo4j_session, boto3_session, account_id, sync_tag, common_job_parameters):
#     logger.info("Trying to autodiscover accounts.")
#     try:
#         # Fetch all accounts
#         client = boto3_session.client('organizations')
#         paginator = client.get_paginator('list_accounts')
#         accounts = []
#         for page in paginator.paginate():
#             accounts.extend(page['Accounts'])

#         # Filter out every account which is not in the ACTIVE status
#         # and select only the Id and Name fields
#         accounts = {x['Name']: x['Id'] for x in accounts if x['Status'] == 'ACTIVE'}

#         # Add them to the graph
#         logger.info("Loading autodiscovered accounts.")
#         tenant.load_aws_accounts(neo4j_session, accounts, sync_tag, common_job_parameters)
#     except botocore.exceptions.ClientError:
#         logger.debug(f"The current account ({account_id}) doesn't have enough permissions to perform autodiscovery.")


def _sync_multiple_subscriptions(neo4j_session, credentials, subscriptions, sync_tag, common_job_parameters):
    logger.debug("Syncing Azure subscriptions: %s", ', '.join(subscriptions.values()))
    tenant.sync(neo4j_session, subscriptions, sync_tag, common_job_parameters)

    for profile_name, subscription_id in subscriptions.items():
        logger.info("Syncing Azure Subscription with ID '%s' using configured profile '%s'.", subscription_id, profile_name)
        common_job_parameters["SUBSCRIPTION_ID"] = subscription_id

        # TODO: populate credentials for a specific subscription

        # _autodiscover_accounts(neo4j_session, boto3_session, subscription_id, sync_tag, common_job_parameters)

        _sync_one_subscription(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters)

    del common_job_parameters["SUBSCRIPTION_ID"]

    # # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # # up those nodes after all AWS accounts have been synced.
    # run_cleanup_job('aws_post_ingestion_principals_cleanup.json', neo4j_session, common_job_parameters)

    # # There may be orphan DNS entries that point outside of known AWS zones. This job cleans
    # # up those entries after all AWS accounts have been synced.
    # run_cleanup_job('aws_post_ingestion_dns_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def start_azure_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
    }

    credentials = None
    subscription_id = None
    tenant_id = None

    try:
        credentials, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    except Exception as e:
        # TODO: change error handling
        logger.debug("Error occurred calling get_azure_cli_credentials().", exc_info=True)
        logger.error(
            (
                "Unable to initialize the default AWS session, an error occurred: %s. Make sure your AWS credentials "
                "are configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return

    if config.azure_sync_all_subscriptions:
        subscriptions = tenant.get_all_azure_subscriptions(credentials)
    else:
        subscriptions = tenant.get_current_azure_subscription(credentials)

    if not subscriptions:
        logger.warning(
            "No valid AWS credentials could be found. No AWS accounts can be synced. Exiting AWS sync stage.",
        )
        return
    if len(list(subscriptions.values())) != len(set(subscriptions.values())):
        logger.warning(
            (
                "There are duplicate AWS accounts in your AWS configuration. It is strongly recommended that you run "
                "cartography with an AWS configuration which has exactly one profile for each AWS account you want to "
                "sync. Doing otherwise will result in undefined and untested behavior."
            ),
        )

    _sync_multiple_subscriptions(neo4j_session, credentials, subscriptions, config.update_tag, common_job_parameters)

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

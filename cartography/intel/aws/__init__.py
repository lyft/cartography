import datetime
import logging
import traceback
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import botocore.exceptions
import neo4j
from neo4j import GraphDatabase

from . import ec2
from . import organizations
from .resources import RESOURCE_FUNCTIONS
from .ec2.util import get_botocore_config
from cartography.config import Config
from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cartography.graph.session import Session

stat_handler = get_stats_client(__name__)
logger = logging.getLogger(__name__)


def _build_aws_sync_kwargs(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    sync_tag: int, common_job_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        'neo4j_session': neo4j_session,
        'boto3_session': boto3_session,
        'regions': regions,
        'current_aws_account_id': current_aws_account_id,
        'update_tag': sync_tag,
        'common_job_parameters': common_job_parameters,
    }


def concurrent_execution(
    service: str, service_func: Any, creds: Dict[str, str], config: Config, neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
):
    logger.info(f"BEGIN processing for service: {service}")

    if creds['type'] == 'self':
        boto3_session = boto3.Session(
            aws_access_key_id=creds['aws_access_key_id'],
            aws_secret_access_key=creds['aws_secret_access_key'],
        )

    elif creds['type'] == 'assumerole':
        boto3_session = boto3.Session(
            aws_access_key_id=creds['aws_access_key_id'],
            aws_secret_access_key=creds['aws_secret_access_key'],
            aws_session_token=creds['session_token'],
        )

    neo4j_auth = (config.neo4j_user, config.neo4j_password)
    neo4j_driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=neo4j_auth,
        max_connection_lifetime=config.neo4j_max_connection_lifetime,
    )

    sync_args = _build_aws_sync_kwargs(
        Session(neo4j_driver), boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters,
    )

    service_func(**sync_args)

    logger.info(f"END processing for service: {service}")


def _sync_one_account(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = [],
    aws_requested_syncs: Iterable[str] = RESOURCE_FUNCTIONS.keys(),
    creds=Dict[str, str],
    config=Config,
) -> None:
    if not regions:
        regions = _autodiscover_account_regions(boto3_session, current_aws_account_id)

    sync_args = _build_aws_sync_kwargs(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters,
    )

    # Process each service in parallel.
    with ThreadPoolExecutor(max_workers=len(RESOURCE_FUNCTIONS) - 2) as executor:
        futures = []

        for func_name in aws_requested_syncs:
            if func_name in RESOURCE_FUNCTIONS:
                # Skip permission relationships and tags for now because they rely on data already being in the graph
                if func_name not in ['permission_relationships', 'resourcegroupstaggingapi']:
                    futures.append(executor.submit(concurrent_execution, func_name,
                                   RESOURCE_FUNCTIONS[func_name], creds, config, **sync_args))
                else:
                    continue
            else:
                raise ValueError(
                    f'AWS sync function "{func_name}" was specified but does not exist. Did you misspell it?')

        for future in as_completed(futures):
            logger.info(f'Result from Future - Service Processing: {future.result()}')

    # MAP IAM permissions
    if 'permission_relationships' in aws_requested_syncs:
        RESOURCE_FUNCTIONS['permission_relationships'](**sync_args)

    # AWS Tags - Must always be last.
    if 'resourcegroupstaggingapi' in aws_requested_syncs:
        RESOURCE_FUNCTIONS['resourcegroupstaggingapi'](config, **sync_args)

    run_analysis_job(
        'aws_ec2_iaminstanceprofile.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_lambda_ecr.json',
        neo4j_session,
        common_job_parameters,
    )
    run_analysis_job(
        'implicit_relationship_creation.json',
        neo4j_session,
        common_job_parameters
    )  # NOTE temp solution (query has to be only executed after both subnet & route table is loaded)

    run_analysis_job(
        'aws_ec2_security_group_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_ec2_subnet_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_ec2_elb_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_ec2_instance_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_ec2_asg_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_ec2_keypair_analysis.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_eks_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_lambda_function_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_s3_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_rds_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_cloudtrail_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_apigateway_asset_exposure.json',
        neo4j_session,
        common_job_parameters
    )

    run_analysis_job(
        'aws_elasticache_cluster_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'aws_redshift_cluster_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='AWSAccount',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )


def _autodiscover_account_regions(boto3_session: boto3.session.Session, account_id: str) -> List[str]:
    regions: List[str] = []
    try:
        regions = ec2.get_ec2_regions(boto3_session)
    except botocore.exceptions.ClientError as e:
        logger.debug("Error occurred getting EC2 regions.", exc_info=True)
        logger.error(
            (
                "Failed to retrieve AWS region list, an error occurred: %s. Could not get regions for account %s."
            ),
            e,
            account_id,
        )
        raise
    return regions


def _autodiscover_accounts(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, account_id: str,
    sync_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Trying to autodiscover accounts.")
    try:
        # Fetch all accounts
        client = boto3_session.client('organizations')
        paginator = client.get_paginator('list_accounts')
        accounts: List[Dict] = []
        for page in paginator.paginate():
            accounts.extend(page['Accounts'])

        # Filter out every account which is not in the ACTIVE status
        # and select only the Id and Name fields
        filtered_accounts: Dict[str, str] = {x['Name']: x['Id'] for x in accounts if x['Status'] == 'ACTIVE'}

        # Add them to the graph
        logger.info("Loading autodiscovered accounts.")
        organizations.load_aws_accounts(neo4j_session, filtered_accounts, sync_tag, common_job_parameters)
    except botocore.exceptions.ClientError:
        logger.warning(f"The current account ({account_id}) doesn't have enough permissions to perform autodiscovery.")


def list_all_regions(boto3_session, logger):
    try:
        client = boto3_session.client('ec2', region_name="us-east-2", config=get_botocore_config())
        regions = client.describe_regions(Filters=[
            {
                'Name': 'opt-in-status',
                'Values': [
                        'opt-in-not-required',
                ]
            },
        ])

    except Exception as e:
        logger.error(f"Failed retrieve enabled regions. Error - {e}")
        return []

    return list(map(lambda region: region['RegionName'], regions['Regions']))


def _sync_multiple_accounts(
    neo4j_session: neo4j.Session,
    accounts: Dict[str, str],
    config: Config,
    common_job_parameters: Dict[str, Any],
    aws_best_effort_mode: bool,
    aws_requested_syncs: List[str] = [],
) -> bool:
    logger.info("Syncing AWS accounts: %s", ', '.join(accounts.values()))
    organizations.sync(neo4j_session, accounts, config.update_tag, common_job_parameters)

    failed_account_ids = []
    exception_tracebacks = []

    num_accounts = len(accounts)

    for profile_name, account_id in accounts.items():
        logger.info("Syncing AWS account with ID '%s' using configured profile '%s'.", account_id, profile_name)
        common_job_parameters["AWS_ID"] = account_id
        # boto3_session = boto3.Session(profile_name=profile_name)

        if config.credentials['type'] == 'self':
            boto3_session = boto3.Session(
                # profile_name=profile_name,
                aws_access_key_id=config.credentials['aws_access_key_id'],
                aws_secret_access_key=config.credentials['aws_secret_access_key'],
            )

        elif config.credentials['type'] == 'assumerole':
            boto3_session = boto3.Session(
                # profile_name=profile_name,
                aws_access_key_id=config.credentials['aws_access_key_id'],
                aws_secret_access_key=config.credentials['aws_secret_access_key'],
                aws_session_token=config.credentials['session_token'],
            )

        _autodiscover_accounts(neo4j_session, boto3_session, account_id, config.update_tag, common_job_parameters)

        # INFO: fetching active regions for customers instead of reading from parameters
        regions = list_all_regions(boto3_session, logger)
        if len(regions) == 0:
            logger.info("regions could not be fetched. reading regions from input parameters")
            regions = config.params.get('regions', [])

        _sync_one_account(
            neo4j_session,
            boto3_session,
            account_id,
            config.update_tag,
            common_job_parameters,
            regions=regions,
            aws_requested_syncs=aws_requested_syncs,  # Could be replaced later with per-account requested syncs
            creds=config.credentials,
            config=config,
        )

    del common_job_parameters["AWS_ID"]
    return True

    # Commented this out to support multi-account setup
    # # There may be orphan Principals which point outside of known AWS accounts. This job cleans
    # # up those nodes after all AWS accounts have been synced.
    # run_cleanup_job('aws_post_ingestion_principals_cleanup.json', neo4j_session, common_job_parameters)

    # # There may be orphan DNS entries that point outside of known AWS zones. This job cleans
    # # up those entries after all AWS accounts have been synced.
    # run_cleanup_job('aws_post_ingestion_dns_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def start_aws_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "permission_relationships_file": config.permission_relationships_file,
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "pagination": {},
        "PUBLIC_PORTS": ['20', '21', '22', '3306', '3389', '4333'],
    }

    try:
        # boto3_session = boto3.Session()

        if config.credentials['type'] == 'self':
            boto3_session = boto3.Session(
                aws_access_key_id=config.credentials['aws_access_key_id'],
                aws_secret_access_key=config.credentials['aws_secret_access_key'],
            )

        elif config.credentials['type'] == 'assumerole':
            boto3_session = boto3.Session(
                aws_access_key_id=config.credentials['aws_access_key_id'],
                aws_secret_access_key=config.credentials['aws_secret_access_key'],
                aws_session_token=config.credentials['session_token'],
            )

    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug("Error occurred calling boto3.Session().", exc_info=True)
        logger.error(
            (
                "Unable to initialize the default AWS session, an error occurred: %s. Make sure your AWS credentials "
                "are configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return

    if config.aws_sync_all_profiles:
        aws_accounts = organizations.get_aws_accounts_from_botocore_config(boto3_session)
    else:
        aws_accounts = organizations.get_aws_account_default(boto3_session)

    if not aws_accounts:
        logger.warning(
            "No valid AWS credentials could be found. No AWS accounts can be synced. Exiting AWS sync stage.",
        )
        return
    if len(list(aws_accounts.values())) != len(set(aws_accounts.values())):
        logger.warning(
            (
                "There are duplicate AWS accounts in your AWS configuration. It is strongly recommended that you run "
                "cartography with an AWS configuration which has exactly one profile for each AWS account you want to "
                "sync. Doing otherwise will result in undefined and untested behavior."
            ),
        )

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.aws_requested_syncs:
        aws_requested_syncs_string = ""
        for service in config.aws_requested_syncs:
            aws_requested_syncs_string += f"{service.get('name', '')},"
            if service.get('pagination', None):
                pagination = service.get('pagination', {})
                pagination['hasNextPage'] = False
                common_job_parameters['pagination'][service.get('name', None)] = pagination
        requested_syncs = parse_and_validate_aws_requested_syncs(aws_requested_syncs_string[:-1])

    sync_successful = _sync_multiple_accounts(
        neo4j_session,
        aws_accounts,
        config,
        common_job_parameters,
        config.aws_best_effort_mode,
        requested_syncs,
    )

    return common_job_parameters

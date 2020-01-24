import logging
from collections import namedtuple

import oci
from oci.exceptions import ConfigFileNotFound, ProfileNotFound, InvalidConfig

#from . import compute
from . import iam
from . import organizations
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job


logger = logging.getLogger(__name__)
Resources = namedtuple('Resources', 'compute iam')

def _sync_one_account(neo4j_session, resources, tenancy_id, oci_sync_tag, common_job_parameters):
    iam.sync(neo4j_session, resources.iam, tenancy_id, oci_sync_tag, common_job_parameters)
    #compute.sync(neo4j_session, resources.compute, tenancy_id, oci_sync_tag, common_job_parameters)

    #Look into adding once DNS records are implemented.
    # NOTE clean up all DNS records, regardless of which job created them
    #run_cleanup_job('OCI_account_dns_cleanup.json', neo4j_session, common_job_parameters)

def _sync_multiple_accounts(neo4j_session, accounts, sync_tag, common_job_parameters):
    logger.debug("Syncing OCI accounts: %s", ', '.join(accounts.keys()))
    organizations.sync(neo4j_session, accounts, sync_tag, common_job_parameters)

    for name in accounts:
        logger.info("Syncing OCI account with ID '%s' using configured profile '%s'.", accounts[name]["tenancy"], name)
        resources = _initialize_resources(accounts[name])
        tenancy_id = accounts[name]["tenancy"]
        common_job_parameters["OCI_TENANCY_ID"] = tenancy_id
        _sync_one_account(neo4j_session, resources, tenancy_id, sync_tag, common_job_parameters)

    del common_job_parameters["OCI_TENANCY_ID"]

    #Look into adding cleanup
    # There may be orphan Users which point outside of known OCI accounts. This job cleans
    # up those nodes after all OCI accounts have been synced.
    #run_cleanup_job('oci_post_ingestion_principals_cleanup.json', neo4j_session, common_job_parameters)
    # There may be orphan DNS entries that point outside of known OCI zones. This job cleans
    # up those entries after all OCI accounts have been synced.
    #run_cleanup_job('oci_post_ingestion_dns_cleanup.json', neo4j_session, common_job_parameters)

def _get_iam_resource(credentials):
    """
    Instantiates a OCI IdentityCleint resource object to call the Identity API. This is used to users,
     ..., ... and ... data. See https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: OCI Credentials object
    :return: A IdentityClient resource object
    """
    return oci.identity.IdentityClient(credentials)

def _get_compute_resource(credentials):
    """
    Instantiates a OCI ComputeClient resource object to call the Compute API. This is used to pull zone, instance, and
    networking data. https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm.
    :param credentials: The OCI Credentials object
    :return: A ComputeClient resource object
    """
    return oci.core.ComputeClient(credentials)

def _initialize_resources(credentials):
    """
    Create namedtuple of all resource objects necessary for OCI data gathering.
    :param credentials: The OCI config object
    :return: namedtuple of all resource objects
    """
    return Resources(
        compute=_get_compute_resource(credentials),
        iam=_get_iam_resource(credentials),
    )

def start_oci_ingestion(neo4j_session, config):
    """
    Starts the OCI ingestion process by initializing OCI Application Default Credentials, creating the necessary
    resource objects, listing all OCI organizations and projects available to the OCI identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    try:
        # Explicitly use Application Default Credentials.
        credentials = oci.config.from_file("~/.oci/config","DEFAULT")
        oci.config.validate_config(credentials)
        #computeClient = oci.core.ComputeClient(credentials)
    except (ConfigFileNotFound, ProfileNotFound, InvalidConfig) as e:
        logger.debug("Error occurred calling oci.config.from_file.", exc_info=True)
        logger.error(
            (
                "Unable to initialize OCI creds. If you don't have OCI data or don't want to load "
                "OCI data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your OCI credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the required Audit policies attached (https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm)."
            ),
            e,
        )
        return


    if config.oci_sync_all_profiles:
        oci_accounts = organizations.get_oci_accounts_from_config()
    else:
        oci_accounts = organizations.get_oci_account_default()

    tenancy_list=[]
    for x in oci_accounts:
        tenancy_list.append(oci_accounts[x]["tenancy"])

    if len(tenancy_list) != len(set(tenancy_list)):
        logger.warning(
            (
                "There are duplicate OCI tenancy's in your OCI configuration. It is strongly recommended that you run "
                "cartography with an OCI configuration which has exactly one profile for each OCI tenancy you want to "
                "sync. Doing otherwise will result in undefined and untested behavior."
            ),
        )

    #I don't think region list is needed at this level.
    #try:
    #    regions = ec2.get_ec2_regions(boto3_session)
    #except botocore.exceptions.ClientError as e:
    #    logger.debug("Error occurred getting OCI Compute regions.", exc_info=True)
    #    logger.error(
    #        (
    #            "Failed to retrieve OCI region list, an error occurred: %s. The OCI sync cannot run without a valid "
    #            "region list."
    #        ),
    #        e,
    #    )
    #    return

    if not oci_accounts:
        logger.warning(
            "No valid OCI credentials could be found. No OCI accounts can be synced. Exiting OCI sync stage.",
        )
        return

    _sync_multiple_accounts(neo4j_session, oci_accounts, config.update_tag, common_job_parameters)

    #Look into adding analysis job once compute is implemented.
    #run_analysis_job(
    #    'oci_compute_asset_exposure.json',
    #    neo4j_session,
    #    common_job_parameters,
    #)

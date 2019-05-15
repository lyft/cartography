from oauth2client.client import GoogleCredentials, ApplicationDefaultCredentialsError
import googleapiclient.discovery
import logging

from cartography.intel.gcp import crm, compute

logger = logging.getLogger(__name__)


def _get_crm_resource_v1(credentials):
    # cache_discovery=False to suppress extra warnings.
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)


def _get_crm_resource_v2(credentials):
    """
    v2 CRM client is required for querying folders
    """
    return googleapiclient.discovery.build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False)


def _get_compute_resource(credentials):
    return googleapiclient.discovery.build('compute', 'v1', credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials):
    return { 'crm_v1': _get_crm_resource_v1(credentials),
             'crm_v2': _get_crm_resource_v2(credentials),
             'compute': _get_compute_resource(credentials) }


def start_gcp_ingestion(session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    try:
        # Explicitly use Application Default Credentials.
        # See https://oauth2client.readthedocs.io/en/latest/source/
        #             oauth2client.client.html#oauth2client.client.OAuth2Credentials
        credentials = GoogleCredentials.get_application_default()
    except ApplicationDefaultCredentialsError as e:
        logger.debug("Error occurred calling GoogleCredentials.get_application_default().", exc_info=True)
        logger.error(
            (
                "Unable to initialize Google Compute Platform creds. If you don't have GCP data or don't want to load "
                "GCP data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your GCP credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the securityReviewer role attached."
            ),
            e
        )
        return
    resources = _initialize_resources(credentials)
    crm.sync_gcp_organizations(session, resources, config.update_tag, common_job_parameters)
    crm.sync_gcp_folders(session, resources, config.update_tag, common_job_parameters)
    crm.sync_gcp_projects(session, resources, config.update_tag, common_job_parameters)
    compute.sync_gcp_instances(session, resources, config.update_tag, common_job_parameters)

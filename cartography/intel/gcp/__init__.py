import json
import logging
from collections import namedtuple
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import googleapiclient.discovery
import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.discovery import HttpError
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.config import Config
from cartography.intel.gcp.auth import AuthHelper
from cartography.intel.gcp import iam
from cartography.intel.gcp import compute
from cartography.intel.gcp import crm
from cartography.intel.gcp import dns
from cartography.intel.gcp import gke
from cartography.intel.gcp import storage
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
Resources = namedtuple('Resources', 'iam compute container crm_v1 crm_v2 dns storage serviceusage')

# Mapping of service short names to their full names as in docs. See https://developers.google.com/apis-explorer,
# and https://cloud.google.com/service-usage/docs/reference/rest/v1/services#ServiceConfig
Services = namedtuple('Services', 'compute storage gke dns iam')
service_names = Services(
    compute='compute.googleapis.com',
    storage='storage.googleapis.com',
    gke='container.googleapis.com',
    dns='dns.googleapis.com',
    iam='iam.googleapis.com',
)


def _get_iam_resource_v1(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google IAM v1 resource object to call the IAM API.
    See https://cloud.google.com/iam/docs/reference/rest.
    :param credentials: The GoogleCredentials object
    :return: A IAM v1 resource object
    """
    # cache_discovery=False to suppress extra warnings.
    return googleapiclient.discovery.build('iam', 'v1', credentials=credentials, cache_discovery=False)


def _get_crm_resource_v1(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v1 resource object to call the Resource Manager API.
    See https://cloud.google.com/resource-manager/reference/rest/.
    :param credentials: The GoogleCredentials object
    :return: A CRM v1 resource object
    """
    # cache_discovery=False to suppress extra warnings.
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)


def _get_crm_resource_v2(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v2 resource object to call the Resource Manager API.
    We need a v2 resource object to query for GCP folders.
    :param credentials: The GoogleCredentials object
    :return: A CRM v2 resource object
    """
    return googleapiclient.discovery.build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False)


def _get_compute_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute resource object to call the Compute API. This is used to pull zone, instance, and
    networking data. See https://cloud.google.com/compute/docs/reference/rest/v1/.
    :param credentials: The GoogleCredentials object
    :return: A Compute resource object
    """
    return googleapiclient.discovery.build('compute', 'v1', credentials=credentials, cache_discovery=False)


def _get_storage_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud Storage resource object to call the Storage API.
    This is used to pull bucket metadata and IAM Policies
    as well as list buckets in a specified project.
    See https://cloud.google.com/storage/docs/json_api/.
    :param credentials: The GoogleCredentials object
    :return: A Storage resource object
    """
    return googleapiclient.discovery.build('storage', 'v1', credentials=credentials, cache_discovery=False)


def _get_container_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud Container resource object to call the
    Container API. See: https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/.

    :param credentials: The GoogleCredentials object
    :return: A Container resource object
    """
    return googleapiclient.discovery.build('container', 'v1', credentials=credentials, cache_discovery=False)


def _get_dns_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud DNS resource object to call the
    Container API. See: https://cloud.google.com/dns/docs/reference/v1/.

    :param credentials: The GoogleCredentials object
    :return: A DNS resource object
    """
    return googleapiclient.discovery.build('dns', 'v1', credentials=credentials, cache_discovery=False)


def _get_serviceusage_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a serviceusage resource object.
    See: https://cloud.google.com/service-usage/docs/reference/rest/v1/operations/list.

    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build('serviceusage', 'v1', credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials: GoogleCredentials) -> Resource:
    """
    Create namedtuple of all resource objects necessary for GCP data gathering.
    :param credentials: The GoogleCredentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        iam=_get_iam_resource_v1(credentials),
        crm_v1=_get_crm_resource_v1(credentials),
        crm_v2=_get_crm_resource_v2(credentials),
        compute=_get_compute_resource(credentials),
        storage=_get_storage_resource(credentials),
        container=_get_container_resource(credentials),
        serviceusage=_get_serviceusage_resource(credentials),
        dns=_get_dns_resource(credentials),
    )


def _services_enabled_on_project(serviceusage: Resource, project_id: str) -> Set:
    """
    Return a list of all Google API services that are enabled on the given project ID.
    See https://cloud.google.com/service-usage/docs/reference/rest/v1/services/list for data shape.
    :param serviceusage: the serviceusage resource provider. See https://cloud.google.com/service-usage/docs/overview.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :return: A set of services that are enabled on the project
    """
    try:
        req = serviceusage.services().list(parent=f'projects/{project_id}', filter='state:ENABLED')
        res = req.execute()
        if 'services' in res:
            return {svc['config']['name'] for svc in res['services']}
        else:
            return set()
    except googleapiclient.discovery.HttpError as http_error:
        http_error = json.loads(http_error.content.decode('utf-8'))
        # This is set to log-level `info` because Google creates many projects under the hood that cartography cannot
        # audit (e.g. adding a script to a Google spreadsheet causes a project to get created) and we don't need to emit
        # a warning for these projects.
        logger.info(
            f"HttpError when trying to get enabled services on project {project_id}. "
            f"Code: {http_error['error']['code']}, Message: {http_error['error']['message']}. "
            f"Skipping.",
        )
        return set()


def _sync_single_project(
    neo4j_session: neo4j.Session, resources: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List[str] = [],
) -> None:
    """
    Handles graph sync for a single GCP project.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    if not regions:
        regions = _auto_discover_regions(resources.compute, project_id)

    # Determine the resources available on the project.
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)

    if service_names.iam in enabled_services:
        iam.sync(neo4j_session, resources.iam, resources.crm_v1, project_id, gcp_update_tag, common_job_parameters, regions)

    if service_names.compute in enabled_services:
        compute.sync(neo4j_session, resources.compute, project_id, gcp_update_tag, common_job_parameters, regions)

    if service_names.storage in enabled_services:
        storage.sync_gcp_buckets(neo4j_session, resources.storage, project_id, gcp_update_tag, common_job_parameters, regions)

    if service_names.gke in enabled_services:
        gke.sync_gke_clusters(neo4j_session, resources.container, project_id, gcp_update_tag, common_job_parameters, regions)

    if service_names.dns in enabled_services:
        dns.sync(neo4j_session, resources.dns, project_id, gcp_update_tag, common_job_parameters, regions)


def _auto_discover_regions(compute: Resource, project_id: str) -> List[Dict]:
    zones = get_zones_in_project(project_id, compute)

    regions = _zones_to_regions(zones)

    return regions


@timeit
def get_zones_in_project(project_id: str, compute: Resource, max_results: Optional[int] = None) -> Optional[List[Dict]]:
    """
    Return the zones where the Compute Engine API is enabled for the given project_id.
    See https://cloud.google.com/compute/docs/reference/rest/v1/zones and
    https://cloud.google.com/compute/docs/reference/rest/v1/zones/list.
    If the API is not enabled or if the project returns a 404-not-found, return None.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :param max_results: Optional cap on number of results returned by this function. Default = None, which means no cap.
    :return: List of a project's zone objects if Compute API is turned on, else None.
    """
    try:
        req = compute.zones().list(project=project_id, maxResults=max_results)
        res = req.execute()
        return res['items']
    except HttpError as e:
        reason = _get_error_reason(e)
        if reason == 'accessNotConfigured':
            logger.info(
                (
                    "Google Compute Engine API access is not configured for project %s; skipping. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        elif reason == 'notFound':
            logger.info(
                (
                    "Project %s returned a 404 not found error. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        elif reason == 'forbidden':
            logger.info(
                (
                    "Your GCP identity does not have the compute.zones.list permission for project %s; skipping "
                    "compute sync for this project. Full details: %s"
                ),
                project_id,
                e,
            )
            return None
        else:
            raise


def _zones_to_regions(zones: List[str]) -> List[Set]:
    """
    Return list of regions from the input list of zones
    :param zones: List of zones. This is the output from `get_zones_in_project()`.
    :return: List of regions available to the project
    """
    regions = set()
    for zone in zones:
        # Chop off the last 2 chars to turn the zone to a region
        region = zone['name'][:-2]     # type: ignore
        regions.add(region)
    return list(regions)     # type: ignore


def _get_error_reason(http_error: HttpError) -> str:
    """
    Helper function to get an error reason out of the googleapiclient's HttpError object
    This function copies the structure of
    https://github.com/googleapis/google-api-python-client/blob/1d2e240a74d2bc0074dffbc57cf7d62b8146cb82/
                                  googleapiclient/http.py#L111
    At the moment this is the best way we know of to extract the HTTP failure reason.
    Additionally, see https://github.com/googleapis/google-api-python-client/issues/662.
    :param http_error: The googleapi HttpError object
    :return: The error reason as a string
    """
    try:
        data = json.loads(http_error.content.decode('utf-8'))
        if isinstance(data, dict):
            reason = data['error']['errors'][0]['reason']
        else:
            reason = data[0]['error']['errors']['reason']
    except (UnicodeDecodeError, ValueError, KeyError):
        logger.warning(f"HttpError: {data}")
        return ''
    return reason


def _sync_multiple_projects(
    neo4j_session: neo4j.Session, resources: Resource, projects: List[Dict],
    gcp_update_tag: int, common_job_parameters: Dict, regions: List[str] = [],
) -> None:
    """
    Handles graph sync for multiple GCP projects.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param: projects: A list of projects. At minimum, this list should contain a list of dicts with the key "projectId"
    defined; so it would look like this: [{"projectId": "my-project-id-12345"}].
    This is the returned data from `crm.get_gcp_projects()`.
    See https://cloud.google.com/resource-manager/reference/rest/v1/projects.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    logger.info("Syncing %d GCP projects.", len(projects))
    crm.sync_gcp_projects(neo4j_session, projects, gcp_update_tag, common_job_parameters)

    for project in projects:
        project_id = project['projectId']
        common_job_parameters["GCP_PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s.", project_id)
        _sync_single_project(neo4j_session, resources, project_id, gcp_update_tag, common_job_parameters, regions=regions)


@timeit
def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the GCP ingestion process by initializing Google Application Default Credentials, creating the necessary
    resource objects, listing all GCP organizations and projects available to the GCP identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "WORKSPACE_ACCOUNT_ID": config.params['workspace']['account_id'],
    }
    try:
        # # Explicitly use Application Default Credentials.
        # # See https://oauth2client.readthedocs.io/en/latest/source/
        # #             oauth2client.client.html#oauth2client.client.OAuth2Credentials
        # credentials = GoogleCredentials.get_application_default()

        auth_helper = AuthHelper()
        credentials = auth_helper.get_credentials(config.credentials['token_uri'], config.credentials['account_email'])

    except ApplicationDefaultCredentialsError as e:
        logger.debug("Error occurred calling GoogleCredentials.get_application_default().", exc_info=True)
        logger.error(
            (
                "Unable to initialize Google Compute Platform creds. If you don't have GCP data or don't want to load "
                "GCP data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your GCP credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the securityReviewer role attached."
            ),
            e,
        )
        return

    resources = _initialize_resources(credentials)

    # If we don't have perms to pull Orgs or Folders from GCP, we will skip safely
    crm.sync_gcp_organizations(neo4j_session, resources.crm_v1, config.update_tag, common_job_parameters)
    crm.sync_gcp_folders(neo4j_session, resources.crm_v2, config.update_tag, common_job_parameters)

    projects = crm.get_gcp_projects(resources.crm_v1)

    # Read regions from parameters
    regions = config.params.get('regions', [])

    _sync_multiple_projects(neo4j_session, resources, projects, config.update_tag, common_job_parameters, regions=regions)

    run_analysis_job(
        'gcp_compute_asset_inet_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'gcp_gke_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        'gcp_gke_basic_auth.json',
        neo4j_session,
        common_job_parameters,
    )

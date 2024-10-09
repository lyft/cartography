import logging
from typing import Dict
from typing import List

import neo4j
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.config import Config
from cartography.intel.gcp import compute, crm, storage, dns, gke
from cartography.util import run_analysis_job
from cartography.util import timeit


logger = logging.getLogger(__name__)



def _sync_multiple_projects(
    neo4j_session: neo4j.Session, projects: List[Dict],
    gcp_update_tag: int, common_job_parameters: Dict, credentials: GoogleCredentials
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
      enabled_services = crm.services_enabled_on_project(project_id)

      if crm.service_names.compute in enabled_services:
        # Compute data sync
        logger.info("Syncing GCP project %s for Compute.", project_id)
        compute.sync_single_project_compute(neo4j_session, project_id, gcp_update_tag, common_job_parameters, credentials)
      if crm.service_names.storage in enabled_services:
        # Storage data sync
        logger.info("Syncing GCP project %s for Storage", project_id)
        storage.sync_single_project_storage(neo4j_session, project_id, gcp_update_tag, common_job_parameters, credentials)
      if crm.service_names.gke in enabled_services:
        # GKE data sync
        logger.info("Syncing GCP project %s for GKE", project_id)
        gke.sync_single_project_gke(neo4j_session, project_id, gcp_update_tag, common_job_parameters, credentials)
      if crm.service_names.dns in enabled_services:
        # DNS data sync
        logger.info("Syncing GCP project %s for DNS", project_id)
        dns.sync_single_project_dns(neo4j_session, project_id, gcp_update_tag, common_job_parameters, credentials)


@timeit
def _get_gcp_credentials() -> GoogleCredentials:
    """
    Gets access tokens for GCP API access.
    :param: None
    :return: GoogleCredentials
    """
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
            e,
        )
        return credentials


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
    }

    credentials = _get_gcp_credentials()

    crm_v1 = crm.get_crm_resource_v1(credentials)
    crm_v2 = crm.get_crm_resource_v2(credentials)
    # If we don't have perms to pull Orgs or Folders from GCP, we will skip safely
    crm.sync_gcp_organizations(neo4j_session, crm_v1, config.update_tag, common_job_parameters, credentials)
    crm.sync_gcp_folders(neo4j_session, crm_v2, config.update_tag, common_job_parameters, credentials)

    projects = crm.get_gcp_projects(crm_v1)

    _sync_multiple_projects(neo4j_session, projects, config.update_tag, common_job_parameters, credentials)

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

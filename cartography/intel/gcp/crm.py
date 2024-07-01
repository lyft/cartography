# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
import logging
from string import Template
from typing import Dict
from typing import List
from collections import namedtuple
import json
from typing import Set

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from oauth2client.client import GoogleCredentials
import googleapiclient.discovery


from cartography.util import timeit
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

Resources = namedtuple('Resources', 'compute container crm_v1 crm_v2 dns storage serviceusage')
# Mapping of service short names to their full names as in docs. See https://developers.google.com/apis-explorer,
# and https://cloud.google.com/service-usage/docs/reference/rest/v1/services#ServiceConfig
Services = namedtuple('Services', 'compute storage gke dns')
service_names = Services(
    compute='compute.googleapis.com',
    storage='storage.googleapis.com',
    gke='container.googleapis.com',
    dns='dns.googleapis.com',
)

def _get_serviceusage_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a serviceusage resource object.
    See: https://cloud.google.com/service-usage/docs/reference/rest/v1/operations/list.

    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build('serviceusage', 'v1', credentials=credentials, cache_discovery=False)

def get_crm_resource_v1(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v1 resource object to call the Resource Manager API.
    See https://cloud.google.com/resource-manager/reference/rest/.
    :param credentials: The GoogleCredentials object
    :return: A CRM v1 resource object
    """
    # cache_discovery=False to suppress extra warnings.
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)


def get_crm_resource_v2(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v2 resource object to call the Resource Manager API.
    We need a v2 resource object to query for GCP folders.
    :param credentials: The GoogleCredentials object
    :return: A CRM v2 resource object
    """
    return googleapiclient.discovery.build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False)


def services_enabled_on_project(serviceusage: Resource, project_id: str) -> Set:
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
        services = set()
        while req is not None:
            res = req.execute()
            if 'services' in res:
                services.update({svc['config']['name'] for svc in res['services']})
            req = serviceusage.services().list_next(previous_request=req, previous_response=res)
        return services
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


@timeit
def get_gcp_organizations(crm_v1: Resource) -> List[Resource]:
    """
    Return list of GCP organizations that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate organizations for any reason.
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP Organizations. See https://cloud.google.com/resource-manager/reference/rest/v1/organizations.
    """
    try:
        req = crm_v1.organizations().search(body={})
        res = req.execute()
        return res.get('organizations', [])
    except HttpError as e:
        logger.warning("HttpError occurred in crm.get_gcp_organizations(), returning empty list. Details: %r", e)
        return []


@timeit
def get_gcp_folders(crm_v2: Resource) -> List[Resource]:
    """
    Return list of GCP folders that the crm_v2 resource object has permissions to access.
    Returns empty list if we are unable to enumerate folders for any reason.
    :param crm_v2: The Compute Resource Manager v2 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP folders. See https://cloud.google.com/resource-manager/reference/rest/v2/folders/list.
    """
    try:
        req = crm_v2.folders().search(body={})
        res = req.execute()
        return res.get('folders', [])
    except HttpError as e:
        logger.warning("HttpError occurred in crm.get_gcp_folders(), returning empty list. Details: %r", e)
        return []


@timeit
def get_gcp_projects(crm_v1: Resource) -> List[Resource]:
    """
    Return list of GCP projects that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate projects for any reason.
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP projects. See https://cloud.google.com/resource-manager/reference/rest/v2/projects/list.
    """
    try:
        projects: List[Resource] = []
        req = crm_v1.projects().list(filter="lifecycleState:ACTIVE")
        while req is not None:
            res = req.execute()
            page = res.get('projects', [])
            projects.extend(page)
            req = crm_v1.projects().list_next(previous_request=req, previous_response=res)
        return projects
    except HttpError as e:
        logger.warning("HttpError occurred in crm.get_gcp_projects(), returning empty list. Details: %r", e)
        return []


@timeit
def load_gcp_organizations(neo4j_session: neo4j.Session, data: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest the GCP organizations to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of organizations; output from crm.get_gcp_organizations()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (org:GCPOrganization{id:$OrgName})
    ON CREATE SET org.firstseen = timestamp()
    SET org.orgname = $OrgName,
    org.displayname = $DisplayName,
    org.lifecyclestate = $LifecycleState,
    org.lastupdated = $gcp_update_tag
    """
    for org_object in data:
        neo4j_session.run(
            query,
            OrgName=org_object['name'],
            DisplayName=org_object.get('displayName', None),
            LifecycleState=org_object.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_folders(neo4j_session: neo4j.Session, data: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest the GCP folders to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of folders; output from crm.get_gcp_folders()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    for folder in data:
        # Get the correct parent type.
        # Parents of folders can only be GCPOrganizations or other folders, see
        # https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
        if folder['parent'].startswith("organizations"):
            query = "MATCH (parent:GCPOrganization{id:$ParentId})"
        elif folder['parent'].startswith("folders"):
            query = """
            MERGE (parent:GCPFolder{id:$ParentId})
            ON CREATE SET parent.firstseen = timestamp()
            """
        query += """
        MERGE (folder:GCPFolder{id:$FolderName})
        ON CREATE SET folder.firstseen = timestamp()
        SET folder.foldername = $FolderName,
        folder.displayname = $DisplayName,
        folder.lifecyclestate = $LifecycleState,
        folder.lastupdated = $gcp_update_tag
        WITH parent, folder
        MERGE (parent)-[r:RESOURCE]->(folder)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        """
        neo4j_session.run(
            query,
            ParentId=folder['parent'],
            FolderName=folder['name'],
            DisplayName=folder.get('displayName', None),
            LifecycleState=folder.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_projects(neo4j_session: neo4j.Session, data: List[Dict], gcp_update_tag: int) -> None:
    """
    Ingest the GCP projects to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of GCP projects; output from crm.get_gcp_projects()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (project:GCPProject{id:$ProjectId})
    ON CREATE SET project.firstseen = timestamp()
    SET project.projectid = $ProjectId,
    project.projectnumber = $ProjectNumber,
    project.displayname = $DisplayName,
    project.lifecyclestate = $LifecycleState,
    project.lastupdated = $gcp_update_tag
    """

    for project in data:
        neo4j_session.run(
            query,
            ProjectId=project['projectId'],
            ProjectNumber=project['projectNumber'],
            DisplayName=project.get('name', None),
            LifecycleState=project.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag,
        )
        if project.get('parent'):
            _attach_gcp_project_parent(neo4j_session, project, gcp_update_tag)


@timeit
def _attach_gcp_project_parent(neo4j_session: neo4j.Session, project: Dict, gcp_update_tag: int) -> None:
    """
    Attach a project to its respective parent, as in the Resource Hierarchy -
    https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
    """
    if project['parent']['type'] == 'organization':
        parent_label = 'GCPOrganization'
    elif project['parent']['type'] == 'folder':
        parent_label = 'GCPFolder'
    else:
        raise NotImplementedError(
            "Ingestion of GCP {}s as parent nodes is currently not supported. "
            "Please file an issue at https://github.com/lyft/cartography/issues.".format(
                project['parent']['type'],
            ),
        )
    parent_id = f"{project['parent']['type']}s/{project['parent']['id']}"
    INGEST_PARENT_TEMPLATE = Template("""
    MATCH (project:GCPProject{id:$ProjectId})

    MERGE (parent:$parent_label{id:$ParentId})
    ON CREATE SET parent.firstseen = timestamp()

    MERGE (parent)-[r:RESOURCE]->(project)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """)
    neo4j_session.run(
        INGEST_PARENT_TEMPLATE.safe_substitute(parent_label=parent_label),
        ParentId=parent_id,
        ProjectId=project['projectId'],
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_organizations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove stale GCP organizations and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job('gcp_crm_organization_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_folders(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove stale GCP folders and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job('gcp_crm_folder_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_projects(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove stale GCP projects and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job('gcp_crm_project_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_gcp_organizations(
    neo4j_session: neo4j.Session, crm_v1: Resource, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(crm_v1)
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    cleanup_gcp_organizations(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_folders(
    neo4j_session: neo4j.Session, crm_v2: Resource, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP folder data using the CRM v2 resource object, load the data to Neo4j, and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param crm_v2: The Compute Resource Manager v2 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(crm_v2)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag)
    cleanup_gcp_folders(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_projects(
    neo4j_session: neo4j.Session, projects: List[Dict], gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Load a given list of GCP project data to Neo4j and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param projects: List of GCP projects; output from crm.get_gcp_projects()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP projects")
    load_gcp_projects(neo4j_session, projects, gcp_update_tag)
    cleanup_gcp_projects(neo4j_session, common_job_parameters)

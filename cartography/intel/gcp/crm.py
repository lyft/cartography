# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_gcp_organizations(crm_v1):
    """
    :param resource: The Resource object created by `googleapiclient.discovery.build()`. See
    https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build and
    https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery.Resource-class.html.
    :return: List of GCP Organizations
    """
    req = crm_v1.organizations().search(body={})
    res = req.execute()
    return res.get('organizations', [])


def get_gcp_folders(crm_v2):
    req = crm_v2.folders().search(body={})
    res = req.execute()
    return res.get('folders', [])


def get_gcp_projects(crm_v1):
    req = crm_v1.projects().list()
    res = req.execute()
    return res.get('projects', [])


def load_gcp_organizations(neo4j_session, data, gcp_update_tag):
    query = """
    MERGE (org:GCPOrganization{id:{OrgName}})
    ON CREATE SET org.firstseen = timestamp()
    SET org.displayname = {DisplayName},
    org.lifecyclestate = {LifecycleState},
    org.lastupdated = {gcp_update_tag}
    """
    for org_object in data:
        neo4j_session.run(
            query,
            OrgName=org_object['name'],
            DisplayName=org_object.get('displayName', None),
            LifecycleState=org_object.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag
        )


def load_gcp_folders(neo4j_session, data, gcp_update_tag):
    """
    {'createTime': '2019-05-14T20:08:46.125Z',
    'displayName': '<my folder name>',
    'lifecycleState': 'ACTIVE',
    'name': 'folders/<Folder ID>',
    'parent': 'organizations/<Org ID>'},
    """
    for folder in data:
        # Get the correct parent type.
        # Parents of folders can only be GCPOrganizations or other folders, see
        # https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
        if folder['parent'].startswith("organizations"):
            query = "MATCH (parent:GCPOrganization{id:{ParentId}})"
        elif folder['parent'].startswith("folders"):
            query = """
            MERGE (parent:GCPFolder{id:{ParentId}})
            ON CREATE SET parent.firstseen = timestamp()
            """
        query += """
        MERGE (folder:GCPFolder{id:{FolderName}})
        ON CREATE SET folder.firstseen = timestamp()
        SET folder.displayname = {DisplayName},
        folder.lifecyclestate = {LifecycleState},
        folder.lastupdated = {gcp_update_tag}
        WITH parent, folder
        MERGE (folder)-[r:PARENT]->(parent)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
        """
        neo4j_session.run(
            query,
            ParentId=folder['parent'],
            FolderName=folder['name'],
            DisplayName=folder.get('displayName', None),
            LifecycleState=folder.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag
        )


def load_gcp_projects(neo4j_session, data, gcp_update_tag):
    """
    {'createTime': '2019-05-14T22:58:03.315Z',
    'lifecycleState': 'ACTIVE',
    'name': 'Friendly name',
    'parent': {'id': '12345', 'type': 'folder'},
    'projectId': 'sys-54321' }
    """
    for project in data:
        if project['parent']['type'] == "organization":
            query = "MATCH (parent:GCPOrganization{id:{ParentId}})"
            parentid = f"organizations/{project['parent']['id']}"
        elif project['parent']['type'] == "folder":
            query = """
            MERGE (parent:GCPFolder{id:{ParentId}})
            ON CREATE SET parent.firstseen = timestamp()
            """
            parentid = f"folders/{project['parent']['id']}"
        query += """
        MERGE (project:GCPProject{id:{ProjectId}})
        ON CREATE SET project.firstseen = timestamp()
        SET project.displayname = {DisplayName},
        project.lifecyclestate = {LifecycleState},
        project.lastupdated = {gcp_update_tag}
        WITH parent, project
        MERGE (project)-[r:PARENT]->(parent)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {gcp_update_tag}
        """
        neo4j_session.run(
            query,
            ParentId=parentid,
            ProjectId=project['projectId'],
            DisplayName=project.get('name', None),
            LifecycleState=project.get('lifecycleState', None),
            gcp_update_tag=gcp_update_tag
        )


def cleanup_gcp_organizations(session, common_job_parameters):
    run_cleanup_job('gcp_crm_organization_cleanup.json', session, common_job_parameters)


def cleanup_gcp_folders(session, common_job_parameters):
    run_cleanup_job('gcp_crm_folder_cleanup.json', session, common_job_parameters)


def cleanup_gcp_projects(session, common_job_parameters):
    run_cleanup_job('gcp_crm_project_cleanup.json', session, common_job_parameters)


def sync_gcp_organizations(session, crm_v1, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(crm_v1)
    load_gcp_organizations(session, data, gcp_update_tag)
    cleanup_gcp_organizations(session, common_job_parameters)


def sync_gcp_folders(session, crm_v2, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(crm_v2)
    load_gcp_folders(session, folders, gcp_update_tag)
    cleanup_gcp_folders(session, common_job_parameters)


def sync_gcp_projects(session, projects, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP projects")
    load_gcp_projects(session, projects, gcp_update_tag)
    cleanup_gcp_projects(session, common_job_parameters)

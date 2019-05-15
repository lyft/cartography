# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy

import googleapiclient.discovery
import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def _get_resource_object(credentials):
    # cache_discovery=False to suppress extra warnings.
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)


def _get_v2_resource_object(credentials):
    """
    v2 CRM client is required for querying folders
    """
    return googleapiclient.discovery.build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False)


def get_gcp_organizations(resource):
    """
    :param resource: The Resource object created by `googleapiclient.discovery.build()`. See
    https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build and
    https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery.Resource-class.html.
    :return: List of GCP Organizations
    """
    req = resource.organizations().search(body={})
    res = req.execute()
    return res['organizations']


def get_gcp_folders(resource):
    req = resource.folders().search(body={})
    res = req.execute()
    return res['folders']


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
        folder.lifecyclestate = {LifecycleState}
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


def cleanup_gcp_organizations(session, common_job_parameters):
    run_cleanup_job('gcp_organization_cleanup.json', session, common_job_parameters)


def cleanup_gcp_folders(session, common_job_parameters):
    #TODO
    #run_cleanup_job('gcp_folder_cleanup.json', session, common_job_parameters)
    pass


def cleanup_gcp_projects(session, common_job_parameters):
    #TODO
    #run_cleanup_job('gcp_folder_cleanup.json', session, common_job_parameters)
    pass


def sync_gcp_organizations(session, credentials, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP organizations")
    crm = _get_resource_object(credentials)

    data = get_gcp_organizations(crm)
    load_gcp_organizations(session, data, gcp_update_tag)
    cleanup_gcp_organizations(session, common_job_parameters)


def sync_gcp_folders(session, credentials, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP folders")
    crmv2 = _get_v2_resource_object(credentials)

    folders = get_gcp_folders(crmv2)
    load_gcp_folders(session, folders, gcp_update_tag)

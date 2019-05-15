# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
from googleapiclient.discovery import HttpError
import json

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
    return res['organizations']


def get_gcp_folders(crm_v2):
    req = crm_v2.folders().search(body={})
    res = req.execute()
    return res['folders']


def get_gcp_projects(crm_v1):
    req = crm_v1.projects().list()
    res = req.execute()
    return res['projects']


def get_zones_in_project(project_id, compute, max_results=None):
    try:
        req = compute.zones().list(project=project_id, maxResults=max_results)
        res = req.execute()
        return res['items']
    except HttpError as e:
        reason = json.loads(e.content)['error']['errors'][0]['reason']
        if reason == 'accessNotConfigured':
            # TODO expose this on the GCPProject node itself
            logger.debug(
                (
                    "Google Compute Engine API access is not configured for project %s. "
                    "Full details: %s"
                ),
                project_id,
                e
            )
            return None
        elif reason == 'notFound':
            logger.debug(
                (
                    "Project %s returned a 404 not found error for some reason. "
                    "Full details: %s"
                ),
                project_id,
                e
            )
            return None
        else:
            logger.error(json.loads(e.content)['error']['errors'][0]['reason'])
            raise e


def get_gce_instances_in_project(project_id, compute):
    """
    Return list of all GCE instances in a given project regardless of zone
    :param project_id: The project id
    :param compute: The compute resource object
    :return: List of all GCE instances in given project regardless of zone
    """
    zones = get_zones_in_project(project_id, compute)
    if not zones:
        return []
    instances = []
    for zone in zones:
        req = compute.instances().list(project=project_id, zone=zone['name'])
        res = req.execute()
        zone_instances = res.get('items', [])
        for instance in zone_instances:
            instance['project_id'] = project_id
            instance['zone_name'] = zone['name']
            instances.append(instance)
    return instances


def _verify_compute_api_is_enabled_for_project(project_id, compute):
    if get_zones_in_project(project_id, compute, max_results=1) == None:
        return False
    else:
        return True


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


def load_gcp_projects(neo4j_session, data, gcp_update_tag):
    """
    {'createTime': '2019-05-14T22:58:03.315Z',
    'lifecycleState': 'ACTIVE',
    'name': 'Lab Compiler',
    'parent': {'id': '1061069017127', 'type': 'folder'},
    'projectId': 'sys-11617012100817884022582786' }
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
        project.lifecyclestate = {LifecycleState}
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


def load_gce_instances(neo4j_session, data, gcp_update_tag):
    query = """
    MATCH (p:GCPProject{id:{ProjectId}})
    MERGE (i:GCEInstance{id:{InstanceId}})
    ON CREATE SET i.firstseen = timestamp()
    SET i.displayname = {DisplayName},
    i.machinetype = {MachineType},
    i.hostname = {Hostname},
    i.zone_name = {ZoneName}
    WITH i, p
    MERGE (p)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for instance in data:
        neo4j_session.run(
            query,
            ProjectId=instance['project_id'],
            InstanceId=instance['id'],
            DisplayName=instance.get('name', None),
            MachineType=instance.get('machineType', None),
            Hostname=instance.get('hostname', None),
            ZoneName=instance['zone_name'],
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


def cleanup_gce_instances(session, common_job_parameters):
    #TODO
    pass


def sync_gcp_organizations(session, resources, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP organizations")
    crm_v1 = resources['crm_v1']

    data = get_gcp_organizations(crm_v1)
    load_gcp_organizations(session, data, gcp_update_tag)
    cleanup_gcp_organizations(session, common_job_parameters)


def sync_gcp_folders(session, resources, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP folders")
    crm_v2 = resources['crm_v2']

    folders = get_gcp_folders(crm_v2)
    load_gcp_folders(session, folders, gcp_update_tag)
    cleanup_gcp_folders(session, common_job_parameters)


def sync_gcp_projects(session, resources, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP projects")
    crm_v1 = resources['crm_v1']

    projects = get_gcp_projects(crm_v1)
    load_gcp_projects(session, projects, gcp_update_tag)
    cleanup_gcp_projects(session, common_job_parameters)


def sync_gce_instances(session, resources, gcp_update_tag, common_job_parameters):
    crm_v1 = resources['crm_v1']
    compute = resources['compute']
    # Note: It could be possible that by the time this function is called there are a different number of GCP projects
    # than in `sync_gcp_projects()`
    projects = get_gcp_projects(crm_v1)
    for project in projects:
        instances = get_gce_instances_in_project(project['projectId'], compute)
        load_gce_instances(session, instances, gcp_update_tag)
        cleanup_gce_instances(session, common_job_parameters)

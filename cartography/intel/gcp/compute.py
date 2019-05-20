# Google Compute Engine API-centric functions
# https://cloud.google.com/compute/docs/concepts
from googleapiclient.discovery import HttpError
import json
import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def _get_error_reason(http_error):
    """
    Helper function to get an error reason out of the googeapiclient's HttpError object
    :param http_error: The googleapi HttpError object
    :return: The error reason as a string
    """
    try:
        data = json.loads(http_error.content.decode('utf-8'))
        if isinstance(data, dict):
            reason = data['error']['reason']
        elif isinstance(data, list) and len(data) > 0:
            first_error = data[0]
            reason = first_error['error']['reason']
    except (ValueError, KeyError, TypeError):
        logger.warning("Could not parse HttpError object, returning `unknown` as reason");
        reason = "unknown"
    return reason


def get_zones_in_project(project_id, compute, max_results=None):
    """
    Return the zones where the Compute Engine API is enabled for the given project_id.
    See https://cloud.google.com/compute/docs/reference/rest/v1/zones and
    https://cloud.google.com/compute/docs/reference/rest/v1/zones/list.

    If the API is not enabled, return None. The message logged in this case looks like this:
    "WARNING:googleapiclient.http:Encountered 403 Forbidden with reason "accessNotConfigured"
    INFO:googleapiclient.discovery:URL being requested:
    GET https://www.googleapis.com/compute/v1/projects/<project_name>/zones?alt=json"
    :param project_id: The project id
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
                        "Project %s returned a 404 not found error. "
                        "Full details: %s"
                    ),
                    project_id,
                    e
                )
                return None
            else:
                logger.error("Could not use Compute Engine API on project %s; Reason: %s".format(project_id, reason))
                raise e



def get_gcp_instances_in_project(project_id, compute):
    """
    Return list of all GCP instances in a given project regardless of zone.
    :param project_id: The project id
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: List of all GCP instances in given project regardless of zone.
    """
    zones = get_zones_in_project(project_id, compute)
    if not zones:
        # If the Compute Engine API is not enabled for a project, there are no zones and therefore no instances.
        return []
    instances = []
    for zone in zones:
        req = compute.instances().list(project=project_id, zone=zone['name'])
        res = req.execute()
        zone_instances = res.get('items', [])
        for instance in zone_instances:
            # Include project_id and zone_name on the `instance` dict so we can load it more easily
            instance['project_id'] = project_id
            instance['zone_name'] = zone['name']
            instances.append(instance)
    return instances


def load_gcp_instances(neo4j_session, data, gcp_update_tag):
    query = """
    MATCH (p:GCPProject{id:{ProjectId}})
    MERGE (i:GCPInstance{id:{InstanceId}})
    ON CREATE SET i.firstseen = timestamp()
    SET i.displayname = {DisplayName},
    i.hostname = {Hostname},
    i.zone_name = {ZoneName},
    i.lastupdated = {gcp_update_tag}
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
            Hostname=instance.get('hostname', None),
            ZoneName=instance['zone_name'],
            gcp_update_tag=gcp_update_tag
        )


def cleanup_gcp_instances(session, common_job_parameters):
    run_cleanup_job('gcp_compute_instance_cleanup.json', session, common_job_parameters)


def sync_gcp_instances(session, compute, project_id, gcp_update_tag, common_job_parameters):
    instances = get_gcp_instances_in_project(project_id, compute)
    load_gcp_instances(session, instances, gcp_update_tag)
    cleanup_gcp_instances(session, common_job_parameters)

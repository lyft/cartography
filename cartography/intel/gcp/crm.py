# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy

import googleapiclient.discovery
import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_gcp_organizations(credentials):
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    # on why we set cache_discovery=False to suppress scary-looking warnings.
    crm = googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)
    req = crm.organizations().search(body={})
    res = req.execute()
    return res['organizations']


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


def cleanup_gcp_organizations(session, common_job_parameters):
    run_cleanup_job('gcp_organization_cleanup.json', session, common_job_parameters)


def sync_organizations(session, credentials, gcp_update_tag, common_job_parameters):
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(credentials)
    load_gcp_organizations(session, data, gcp_update_tag)
    cleanup_gcp_organizations(session, common_job_parameters)

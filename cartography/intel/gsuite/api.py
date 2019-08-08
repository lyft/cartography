import logging

from googleapiclient.discovery import HttpError


logger = logging.getLogger(__name__)


def get_all_groups(admin):
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the users for any reasons

    :param admin: apiclient discovery resource object
    See
    :return: List of Google groups in domain

    """
    request = admin.groups().list(customer='my_customer', maxResults=200, orderBy='email')
    groups = []
    while request is not None:
        try:
            resp = request.execute()
        except HttpError as e:
            logger.warning('HttpError occurred in api.get_all_groups(), returning empty list. Details: %r', e)
            groups = []
            break
        groups = groups + resp.get('groups', [])
        request = admin.groups().list_next(request, resp)
    return groups


def get_all_users(admin):
    """
    Return list of Google Users in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param admin: apiclient discovery resource object
    see
    :return: List of Google users in domain
    see https://developers.google.com/admin-sdk/directory/v1/guides/manage-users#get_all_domain_users
    """

    request = admin.users().list(customer='my_customer', maxResults=500, orderBy='email')
    users = []
    while request is not None:
        try:
            resp = request.execute()
        except HttpError as e:
            logger.warning('HttpError occurred in api.get_all_users(), returning empty list. Details: %r', e)
            users = []
            break
        users = users + resp.get('users', [])
        request = admin.users().list_next(request, resp)
    return users


def load_gsuite_groups(session, users, gcp_update_tag):
    # XXX: TODO
    pass


def load_gsuite_users(session, users, gcp_update_tag):
    # XXX: TODO
    pass


def cleanup_gsuite_users(session, common_job_parameters):
    # XXX: TODO
    pass


def cleanup_gsuite_groups(session, common_job_parameters):
    # XXX: TODO
    pass


def sync_gsuite_users(session, admin, gsuite_update_tag, common_job_parameters):
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    :param session: The Neo4j session
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Users')
    users = get_all_users(admin)
    load_gsuite_users(session, users, gsuite_update_tag)
    cleanup_gsuite_users(session, common_job_parameters)


def sync_gsuite_groups(session, admin, gsuite_update_tag, common_job_parameters):
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    :param session: The Neo4j session
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Groups')
    groups = get_all_groups(admin)
    load_gsuite_groups(session, groups, gsuite_update_tag)
    cleanup_gsuite_groups(session, common_job_parameters)

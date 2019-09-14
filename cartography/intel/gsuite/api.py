import logging

from googleapiclient.discovery import HttpError

from cartography.util import run_cleanup_job


logger = logging.getLogger(__name__)


def get_all_groups(admin):
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of Google groups in domain
    """
    return repeat_request(
        req=admin.groups().list,
        req_args={'customer': 'my_customer', 'maxResults': 200, 'orderBy': 'email'},
        req_next=admin.groups().list_next,
    )


def transform_api_objects(response_objects, key):
    """ Helper method to strip list of API response objects from its request metadata.
    Returns list of dictionaries of the core objects we're interested in such as users, groups, members.

    Example:
    {kind':'admin#directory#users',
    'etag': 'SXFHf...',
    'nextPageToken': '0a30f...'
    'users': [{...}]}

    This function would return a concatenated list of the 'users' key.

    :param response_objects: list of raw response objects from the GSuite API
    :param key: where the core objects live
    :return: list of dictionary objects as defined in /docs/schema/gsuite.md
    """
    groups = []
    for response_object in response_objects:
        for group in response_object.get(key, []):
            groups.append(group)
    return groups


def repeat_request(req, req_args, req_next, retries=5):
    """ Wrapper to retry requests.  We make a lot of requests to Google.
    Sometimes it may flake out due to network or server issues.  Repeat if it fails.

    :param req: The API request to make
    :param req_args: The API request arguments
    :param req_next: API request for paginatioon
    :param retries: number of retries to attempt
    :return: list of Google API object models
    """
    retry = 0
    request = req(**req_args)
    response_objects = []
    while request is not None:
        try:
            resp = request.execute()
            response_objects.append(resp)
            request = req_next(request, resp)
        except HttpError as e:
            logger.warning(f'HttpError occurred returning empty list. Details: {e}, retry: {retry}')
            retry += 1
            if retry >= retries:
                break
    return response_objects


def get_members_for_group(admin, group_email):
    """ Get all members for a google group

    :param group_email: A string representing the email address for the group

    :return: List of dictionaries representing Users or Groups.
    """
    return repeat_request(
        req=admin.members().list,
        req_args={'groupKey': group_email, 'maxResults': 500},
        req_next=admin.members().list_next,
    )


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
    return repeat_request(
        req=admin.users().list,
        req_args={'customer': 'my_customer', 'maxResults': 500, 'orderBy': 'email'},
        req_next=admin.users().list_next,
    )


def load_gsuite_groups(session, groups, gsuite_update_tag):
    ingestion_qry = """
        UNWIND {GroupData} as group
        MERGE (g:GSuiteGroup{id: group.id})
        ON CREATE SET
        g.firstseen = {UpdateTag}
        ON MATCH SET
        g.group_id = group.id,
        g.admin_created = group.adminCreated,
        g.description = group.description,
        g.direct_members_count = group.directMembersCount,
        g.email = group.email,
        g.etag = group.etag,
        g.kind = group.kind,
        g.name = group.name,
        g.lastupdated = {UpdateTag}
    """
    logger.info('Ingesting {} gsuite groups'.format(len(groups)))
    session.run(ingestion_qry, GroupData=groups, UpdateTag=gsuite_update_tag)


def load_gsuite_users(session, users, gsuite_update_tag):
    ingestion_qry = """
        UNWIND {UserData} as user
        MERGE (u:GSuiteUser{id: user.id})
        ON CREATE SET
        u.firstseen = {UpdateTag}
        ON MATCH SET
        u.user_id = user.id,
        u.agreed_to_terms = user.agreedToTerms,
        u.archived = user.archived,
        u.change_password_at_next_login = user.changePasswordAtNextLogin,
        u.creation_time = user.creationTime,
        u.customer_id = user.customerId,
        u.etag = user.etag,
        u.include_in_global_address_list = user.includeInGlobalAddressList,
        u.ip_whitelisted = user.ipWhitelisted,
        u.is_admin = user.isAdmin,
        u.is_delegated_admin =  user.isDelegatedAdmin,
        u.is_enforced_in_2_sv = user.isEnforcedIn2Sv,
        u.is_enrolled_in_2_sv = user.isEnrolledIn2Sv,
        u.is_mailbox_setup = user.isMailboxSetup,
        u.kind = user.kind,
        u.last_login_time = user.lastLoginTime,
        u.name = user.name.fullName,
        u.family_name = user.name.familyName,
        u.given_name = user.name.givenName,
        u.org_unit_path = user.orgUnitPath,
        u.primary_email = user.primaryEmail,
        u.email = user.primaryEmail,
        u.suspended = user.suspended,
        u.thumbnail_photo_etag = user.thumbnailPhotoEtag,
        u.thumbnail_photo_url = user.thumbnailPhotoUrl,
        u.lastupdated = {UpdateTag}
    """
    logger.info('Ingesting {} gsuite users'.format(len(users)))
    session.run(ingestion_qry, UserData=users, UpdateTag=gsuite_update_tag)


def load_gsuite_members(session, group, members, gsuite_update_tag):
    print(f"Creating members relationship {len(members)}")
    ingestion_qry = """
        UNWIND {MemberData} as member
        MATCH (user:GSuiteUser {id: member.id}),(group:GSuiteGroup {id: {GroupID} })
        MERGE (user)-[r:MEMBER_GSUITE_GROUP]->(group)
        ON CREATE SET
        r.firstseen = {UpdateTag}
        ON MATCH SET
        r.lastupdated = {UpdateTag}
    """
    session.run(
        ingestion_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
    )
    membership_qry = """
        UNWIND {MemberData} as member
        MATCH(group_1: GSuiteGroup{id: member.id}), (group_2:GSuiteGroup {id: {GroupID}})
        MERGE (group_1)-[r:MEMBER_GSUITE_GROUP]->(group_2)
        ON CREATE SET
        r.firstseen = {UpdateTag}
        ON MATCH SET
        r.lastupdated = {UpdateTag}
    """
    session.run(membership_qry, MemberData=members, GroupID=group.get("id"), UpdateTag=gsuite_update_tag)


def cleanup_gsuite_users(session, common_job_parameters):
    run_cleanup_job(
        'gsuite_ingest_users_cleanup.json',
        session,
        common_job_parameters,
    )


def cleanup_gsuite_groups(session, common_job_parameters):
    run_cleanup_job(
        'gsuite_ingest_groups_cleanup.json',
        session,
        common_job_parameters,
    )


def sync_gsuite_users(session, admin, gsuite_update_tag, common_job_parameters):
    """
    GET GSuite user objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Users')
    resp_objs = get_all_users(admin)
    users = transform_api_objects(resp_objs, 'users')
    load_gsuite_users(session, users, gsuite_update_tag)
    cleanup_gsuite_users(session, common_job_parameters)


def sync_gsuite_groups(session, admin, gsuite_update_tag, common_job_parameters):
    """
    GET GSuite group objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Groups')
    resp_objs = get_all_groups(admin)
    groups = transform_api_objects(resp_objs, 'groups')
    load_gsuite_groups(session, groups, gsuite_update_tag)
    cleanup_gsuite_groups(session, common_job_parameters)
    sync_gsuite_members(groups, session, admin, gsuite_update_tag)


def sync_gsuite_members(groups, session, admin, gsuite_update_tag):
    for group in groups:
        resp_objs = get_members_for_group(admin, group['email'])
        members = transform_api_objects(resp_objs, 'members')
        load_gsuite_members(session, group, members, gsuite_update_tag)

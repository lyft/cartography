import logging

from googleapiclient.discovery import HttpError


logger = logging.getLogger(__name__)


def get_all_groups(admin):
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    :param admin: apiclient discovery resource object
    See
    :return: List of Google groups in domain

    """
    request = admin.groups().list(customer='my_customer', maxResults=20, orderBy='email')
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


def get_all_groups_for_email(admin, email):
    """ Fetch all groups of which the given group is a member

    Arguments:
        email: A string representing the email address for the group

    Returns a list of Group models
    Throws GoogleException
    """
    request = admin.groups().list(userKey=email, maxResults=500)
    groups = []
    while request is not None:
        try:
            resp = request.execute()
        except HttpError as e:
            logger.warning('HttpError occurred in api.get_groups_for_email(), returning empty list. Details: %r', e)
            groups = []
            break
        groups = groups + resp.get('groups', [])
        request = admin.groups().list_next(request, resp)
    return groups


def get_members_for_group(admin, group_email):
    """ Get all members for a google group

    :param group_email: A string representing the email address for the group

    :return: List of dictionaries representing Users or Groups.
    """
    request = admin.members().list(
        groupKey=group_email,
        maxResults=500,
    )
    members = []
    while request is not None:
        try:
            resp = request.execute()
        except HttpError as e:
            logger.warning('HttpError occurred in api.get_members_for_group(), returning empty list. Details: %r', e)
            members = []
            break
        members = members + resp.get('members', [])
        request = admin.members().list_next(request, resp)

    return members


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
        # break
        request = admin.users().list_next(request, resp)
    return users


def load_gsuite_groups(session, groups, gsuite_update_tag):
    ingestion_qry = """
        UNWIND {GroupData} as group
        MERGE (g:GSuiteGroup{id: group.id})
        ON CREATE SET
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
        u.suspended = user.suspended,
        u.thumbnail_photo_etag = user.thumbnailPhotoEtag,
        u.thumbnail_photo_url = user.thumbnailPhotoUrl,
        u.lastupdated = {UpdateTag}
    """
    logger.info('Ingesting {} gsuite users'.format(len(users)))
    session.run(ingestion_qry, UserData=users, UpdateTag=gsuite_update_tag)


def load_gsuite_members(session, group, members, gsuite_update_tag):
    # for member in members:
    print(f"Creating members relationship {len(members)}")
    ingestion_qry = """
        UNWIND {MemberData} as member
        MATCH (user:GSuiteUser {id: member.id}),(group:GSuiteGroup {id: {GroupID} })
        MERGE (user)-[r:MEMBER_GSUITE_GROUP]->(group)
    """
    session.run(
        ingestion_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
    )

    membership_qry = """
        UNWIND {MemberData} as member
        MATCH(user: GSuiteGroup{id: member.id}), (group:GSuiteGroup {id: {GroupID}})
        MERGE (user)-[r:MEMBER_GSUITE_GROUP]->(group)
    """
    session.run(membership_qry, MemberData=members, GroupID=group.get("id"), UpdateTag=gsuite_update_tag)


def cleanup_gsuite_users(session, common_job_parameters):
    # XXX: TODO
    pass


def cleanup_gsuite_groups(session, common_job_parameters):
    # XXX: TODO
    pass


def sync_gsuite_users(session, admin, gsuite_update_tag, common_job_parameters):
    """

    """
    logger.debug('Syncing GSuite Users')
    users = get_all_users(admin)
    load_gsuite_users(session, users, gsuite_update_tag)
    cleanup_gsuite_users(session, common_job_parameters)


def sync_gsuite_groups(session, admin, gsuite_update_tag, common_job_parameters):
    """

    """
    logger.debug('Syncing GSuite Groups')
    groups = get_all_groups(admin)
    load_gsuite_groups(session, groups, gsuite_update_tag)
    cleanup_gsuite_groups(session, common_job_parameters)
    sync_gsuite_members(groups, session, admin, gsuite_update_tag)


def sync_gsuite_members(groups, session, admin, gsuite_update_tag):
    for group in groups:
        members = get_members_for_group(admin, group['email'])
        load_gsuite_members(session, group, members, gsuite_update_tag)

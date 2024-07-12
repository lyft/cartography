
import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)


GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_users(admin: Resource, project_id: str) -> List[Dict]:
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
    response_objects = []
    try:
        while request is not None:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = admin.users().list_next(request, resp)
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        logger.warning(
            (
                "Could not retrieve users on project %s due to issue. Code: %s, Message: %s"
            ), project_id, err['code'], err['message'],
        )

    return response_objects


@timeit
def transform_users(response_objects: List[Dict]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only
    :param response_objects:
    :return: list of dictionary objects as defined in /docs/schema/gsuite.md
    """
    users: List[Dict] = []
    for response_object in response_objects:
        for user in response_object['users']:
            users.append(user)
    return users


@timeit
def get_all_groups(admin: Resource, project_id: str) -> List[Dict]:
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of Google groups in domain
    """
    request = admin.groups().list(customer='my_customer', maxResults=20, orderBy='email')
    response_objects = []
    try:
        while request is not None:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = admin.groups().list_next(request, resp)
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        logger.warning(
            (
                "Could not retrieve groups on project %s due to issue. Code: %s, Message: %s"
            ), project_id, err['code'], err['message'],
        )
    return response_objects


@timeit
def transform_groups(response_objects: List[Dict]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only

    :param response_objects:
    :return: list of dictionary objects as defined in /docs/schema/gsuite.md
    """
    groups: List[Dict] = []
    for response_object in response_objects:
        for group in response_object['groups']:
            groups.append(group)
    return groups


@timeit
def get_users(admin: Resource) -> List[Dict]:
    users = []
    try:
        req = admin.users().list(customer="my_customer")
        while req is not None:
            res = req.execute()
            page = res.get('users', [])
            users.extend(page)
            req = admin.users().list_next(previous_request=req, previous_response=res)
        return users
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve users due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_members_for_group(admin: Resource, group_email: str) -> List[Dict]:
    """ Get all members for a google group

    :param group_email: A string representing the email address for the group

    :return: List of dictionaries representing Users or Groups.
    """
    request = admin.members().list(
        groupKey=group_email,
        maxResults=500,
    )
    members: List[Dict] = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        members = members + resp.get('members', [])
        request = admin.members().list_next(request, resp)

    return members


@timeit
def get_groups(admin: Resource) -> List[Dict]:
    groups = []
    try:
        req = admin.groups().list()
        while req is not None:
            res = req.execute()
            page = res.get('groups', [])
            groups.extend(page)
            req = admin.groups().list_next(previous_request=req, previous_response=res)
        return groups
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve groups due to permissions issue. Code: %s, Message: %s"
                ), err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_users(session: neo4j.Session, data_list: List[Dict], organization_id: str, update_tag: int) -> None:
    session.write_transaction(_load_users_tx, data_list, organization_id, update_tag)


@timeit
def _load_users_tx(tx: neo4j.Transaction, users: List[Dict], organization_id: str, gcp_update_tag: int) -> None:
    ingest_users = """
    UNWIND $users as usr
    MERGE (user:GCPUser{id:usr.primaryEmail})
    ON CREATE SET
        user:GCPPrincipal,
        user.firstseen = timestamp()
    SET
        user.userId = usr.id,
        user.email = usr.primaryEmail,
        user.isAdmin = usr.isAdmin,
        user.isDelegatedAdmin = usr.isDelegatedAdmin,
        user.agreedToTerms = usr.agreedToTerms,
        user.suspended = usr.suspended,
        user.changePasswordAtNextLogin = usr.changePasswordAtNextLogin,
        user.ipWhitelisted = usr.ipWhitelisted,
        user.name = usr.name.fullName,
        user.familyName = usr.name.familyName,
        user.givenName = usr.name.givenName,
        user.isMailboxSetup = usr.isMailboxSetup,
        user.customerId = usr.customerId,
        user.addresses = usr.addresses,
        user.organizations = usr.organizations,
        user.lastLoginTime = usr.lastLoginTime,
        user.suspensionReason = usr.suspensionReason,
        user.creationTime = usr.creationTime,
        user.deletionTime = usr.deletionTime,
        user.gender = usr.gender,
        user.lastupdated = $gcp_update_tag
    WITH user, usr
    MATCH (o:GCPOrganization{id: $organization_id})
    MERGE (o)-[r:RESOURCE]->(user)
    ON CREATE SET
        r.firstseen = timestamp()
    SET
        r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_users,
        users=users,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_users(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_users_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_groups(session: neo4j.Session, data_list: List[Dict], organization_id: str, update_tag: int) -> None:
    session.write_transaction(_load_groups_tx, data_list, organization_id, update_tag)


@timeit
def _load_groups_tx(tx: neo4j.Transaction, groups: List[Dict], organization_id: str, gcp_update_tag: int) -> None:
    ingest_groups = """
    UNWIND $groups as grp
    MERGE (group:GCPGroup{id:grp.email})
    ON CREATE SET
        group:GCPPrincipal,
        group.firstseen = timestamp()
    SET
        group.groupId = grp.id,
        group.email = grp.email,
        group.adminCreated = grp.adminCreated,
        group.directMembersCount = grp.directMembersCount,
        group.lastupdated = $gcp_update_tag
    WITH group,grp
    MATCH (o:GCPOrganization{id: $organization_id})
    MERGE (o)-[r:RESOURCE]->(group)
    ON CREATE SET
        r.firstseen = timestamp()
    SET
        r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_groups,
        groups=groups,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_groups_members(neo4j_session: neo4j.Session, group: Dict, members: List[Dict], gsuite_update_tag: int) -> None:
    ingestion_qry = """
        UNWIND $MemberData as member
        MATCH (user:GCPUser {userId: member.id}),(group:GCPGroup {groupId: $GroupID })
        MERGE (user)-[r:MEMBER_GROUP]->(group)
        ON CREATE SET
        r.firstseen = $UpdateTag
        SET
        r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        ingestion_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
    )
    membership_qry = """
        UNWIND $MemberData as member
        MATCH(group_1: GCPGroup{groupId: member.id}), (group_2:GCPGroup {groupId: $GroupID})
        MERGE (group_1)-[r:MEMBER_GROUP]->(group_2)
        ON CREATE SET
        r.firstseen = timestamp()
        SET
        r.lastupdated = $UpdateTag
    """
    neo4j_session.run(membership_qry, MemberData=members, GroupID=group.get("id"), UpdateTag=gsuite_update_tag)


@timeit
def cleanup_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_groups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_groups_members(
    groups: List[Dict], neo4j_session: neo4j.Session, admin: Resource, gsuite_update_tag: int,
) -> None:
    for group in groups:
        members = get_members_for_group(admin, group['email'])
        load_groups_members(neo4j_session, group, members, gsuite_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, admin: Resource,
    project_id: str, gcp_update_tag: int, common_job_parameters: Dict, regions: List,
) -> None:
    logger.info("Syncing workspace objects for project %s.", project_id)

    users_response_objects = get_all_users(admin, project_id)
    users = transform_users(response_objects=users_response_objects)
    gcp_organization_id = common_job_parameters['GCP_ORGANIZATION_ID']
    load_users(neo4j_session, users, gcp_organization_id, gcp_update_tag)
    cleanup_users(neo4j_session, common_job_parameters)

    groups_response_objects = get_all_groups(admin, project_id)
    groups = transform_groups(response_objects=groups_response_objects)
    load_groups(neo4j_session, groups, gcp_organization_id, gcp_update_tag)
    sync_groups_members(groups, neo4j_session, admin, gcp_update_tag)
    cleanup_groups(neo4j_session, common_job_parameters)

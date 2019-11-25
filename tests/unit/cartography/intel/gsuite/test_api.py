from unittest import mock
from unittest.mock import patch

import pytest
from googleapiclient.discovery import HttpError

from cartography.intel.gsuite import api
from cartography.intel.helper.google_request import GoogleRetryException


def test_repeat_request():
    req = mock.MagicMock()
    req_args = {'test': '123'}
    req_next = mock.MagicMock()
    raw_req_1 = mock.MagicMock()
    resp_req_1 = {'users': [1, 2]}
    raw_req_2 = mock.MagicMock()
    resp_req_2 = {'users': [3]}

    req.return_value = raw_req_1
    req_next.side_effect = [raw_req_2, None]

    raw_req_1.execute.return_value = resp_req_1
    raw_req_2.execute.return_value = resp_req_2

    result = api.repeat_request(req, req_args, req_next, retries=5)
    expected = [resp_req_1, resp_req_2]
    assert result == expected


@patch('time.sleep')
def test_repeat_request_failure(patched_sleep):
    # Test that we retry a failed request n-times on HttpError
    req = mock.MagicMock()
    req_args = {'test': '123'}
    req_next = mock.MagicMock()
    raw_req_1 = mock.MagicMock()
    resp_req_1 = {'users': [1, 2]}

    req.return_value = raw_req_1
    raw_req_1.execute.return_value = resp_req_1

    raw_req_1.execute.side_effect = HttpError(mock.Mock(status=503), content=b'Service Unavailable')
    with pytest.raises(GoogleRetryException):
        api.repeat_request(req, req_args, req_next, retries=3)
        assert raw_req_1.execute.call_count == 3
        assert patched_sleep.called


def test_transform_api_objects():
    resp_objs = [
        {
            'a': '1',
            'b': '2',
            'c': ['x'],
        },
        {
            'a': '1',
            'c': ['y', 'z'],
        },
    ]
    expected = ['x', 'y', 'z']
    result = api.transform_api_objects(resp_objs, 'c')
    assert result == expected


@patch(
    'cartography.intel.gsuite.api.repeat_request', return_value=[
        {'users': [{'primaryEmail': 'employee1@test.lyft.com'}, {'primaryEmail': 'employee2@test.lyft.com'}]},
        {'users': [{'primaryEmail': 'employee3@test.lyft.com'}]},
    ],
)
def test_get_all_users(repeat_requests):
    client = mock.MagicMock()
    result = api.get_all_users(client)
    api.transform_api_objects(result, 'users')
    repeat_requests.assert_called_once()
    emails = [user['primaryEmail'] for response_object in result for user in response_object['users']]

    expected = [
        'employee1@test.lyft.com',
        'employee2@test.lyft.com',
        'employee3@test.lyft.com',
    ]
    assert sorted(emails) == sorted(expected)


@patch(
    'cartography.intel.gsuite.api.repeat_request', return_value=[
        {'groups': [{'email': 'group1@test.lyft.com'}, {'email': 'group2@test.lyft.com'}]},
        {'groups': [{'email': 'group3@test.lyft.com'}]},
    ],
)
def test_get_all_groups(repeat_requests):
    client = mock.MagicMock()
    result = api.get_all_groups(client)
    repeat_requests.assert_called_once()
    repeat_requests.assert_called_with(
        req=client.groups().list,
        req_args={'customer': 'my_customer', 'maxResults': 200, 'orderBy': 'email'},
        req_next=client.groups().list_next,
    )
    emails = [group['email'] for response_object in result for group in response_object['groups']]

    expected = [
        'group1@test.lyft.com',
        'group2@test.lyft.com',
        'group3@test.lyft.com',
    ]
    assert sorted(emails) == sorted(expected)


@patch('cartography.intel.gsuite.api.cleanup_gsuite_users')
@patch('cartography.intel.gsuite.api.load_gsuite_users')
@patch(
    'cartography.intel.gsuite.api.get_all_users', return_value=[
        {'users': [{'primaryEmail': 'group1@test.lyft.com'}, {'primaryEmail': 'group2@test.lyft.com'}]},
        {'users': [{'primaryEmail': 'group3@test.lyft.com'}, {'primaryEmail': 'group4@test.lyft.com'}]},
    ],
)
def test_sync_gsuite_users(get_all_users, load_gsuite_users, cleanup_gsuite_users):
    client = mock.MagicMock()
    gsuite_update_tag = 1
    session = mock.MagicMock()
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_users(session, client, gsuite_update_tag, common_job_param)
    users = api.transform_api_objects(get_all_users(), 'users')
    load_gsuite_users.assert_called_with(
        session, users, gsuite_update_tag,
    )
    cleanup_gsuite_users.assert_called_once()


@patch('cartography.intel.gsuite.api.sync_gsuite_members')
@patch('cartography.intel.gsuite.api.cleanup_gsuite_groups')
@patch('cartography.intel.gsuite.api.load_gsuite_groups')
@patch(
    'cartography.intel.gsuite.api.get_all_groups', return_value=[
        {'groups': [{'email': 'group1@test.lyft.com'}, {'email': 'group2@test.lyft.com'}]},
        {'groups': [{'email': 'group3@test.lyft.com'}, {'email': 'group4@test.lyft.com'}]},
    ],
)
def test_sync_gsuite_groups(all_groups, load_gsuite_groups, cleanup_gsuite_groups, sync_gsuite_members):
    admin_client = mock.MagicMock()
    session = mock.MagicMock()
    gsuite_update_tag = 1
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_groups(session, admin_client, gsuite_update_tag, common_job_param)
    groups = api.transform_api_objects(all_groups(), 'groups')
    load_gsuite_groups.assert_called_with(session, groups, gsuite_update_tag,)
    cleanup_gsuite_groups.assert_called_once()
    sync_gsuite_members.assert_called_with(groups, session, admin_client, gsuite_update_tag)


def test_load_gsuite_groups():
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
    groups = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_groups(session, groups, update_tag)
    session.run.assert_called_with(
        ingestion_qry,
        GroupData=groups,
        UpdateTag=update_tag,
    )


def test_load_gsuite_users():
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
    users = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_users(session, users, update_tag)
    session.run.assert_called_with(
        ingestion_qry,
        UserData=users,
        UpdateTag=update_tag,
    )


def test_transform_groups():
    param = [
        {'groups': [{'email': 'group1@test.lyft.com'}, {'email': 'group2@test.lyft.com'}]},
        {'groups': [{'email': 'group3@test.lyft.com'}, {'email': 'group4@test.lyft.com'}]},
    ]
    expected = [
        {'email': 'group1@test.lyft.com'}, {'email': 'group2@test.lyft.com'},
        {'email': 'group3@test.lyft.com'}, {'email': 'group4@test.lyft.com'},
    ]
    result = api.transform_api_objects(param, 'groups')
    assert result == expected


def test_transform_users():
    param = [
        {'users': [{'primaryEmail': 'group1@test.lyft.com'}, {'primaryEmail': 'group2@test.lyft.com'}]},
        {'users': [{'primaryEmail': 'group3@test.lyft.com'}, {'primaryEmail': 'group4@test.lyft.com'}]},
    ]
    expected = [
        {'primaryEmail': 'group1@test.lyft.com'}, {'primaryEmail': 'group2@test.lyft.com'},
        {'primaryEmail': 'group3@test.lyft.com'}, {'primaryEmail': 'group4@test.lyft.com'},
    ]
    result = api.transform_api_objects(param, 'users')
    assert result == expected

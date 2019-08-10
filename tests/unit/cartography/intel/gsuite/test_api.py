from unittest import mock
from unittest.mock import patch

from cartography.intel.gsuite import api


def test_get_all_users():
    client = mock.MagicMock()
    raw_request_1 = mock.MagicMock()
    raw_request_2 = mock.MagicMock()

    user1 = {'primaryEmail': 'employee1@test.lyft.com'}
    user2 = {'primaryEmail': 'employee2@test.lyft.com'}
    user3 = {'primaryEmail': 'employee3@test.lyft.com'}

    client.users().list.return_value = raw_request_1
    client.users().list_next.side_effect = [raw_request_2, None]

    raw_request_1.execute.return_value = {'users': [user1, user2]}
    raw_request_2.execute.return_value = {'users': [user3]}

    result = api.get_all_users(client)
    emails = [u['primaryEmail'] for u in result]

    expected = [
        'employee1@test.lyft.com',
        'employee2@test.lyft.com',
        'employee3@test.lyft.com',
    ]
    assert sorted(emails) == sorted(expected)


def test_get_all_groups():
    client = mock.MagicMock()
    raw_request_1 = mock.MagicMock()
    raw_request_2 = mock.MagicMock()

    group1 = {'email': 'group1@test.lyft.com'}
    group2 = {'email': 'group2@test.lyft.com'}
    group3 = {'email': 'group3@test.lyft.com'}

    client.groups().list.return_value = raw_request_1
    client.groups().list_next.side_effect = [raw_request_2, None]

    raw_request_1.execute.return_value = {'groups': [group1, group2]}
    raw_request_2.execute.return_value = {'groups': [group3]}

    result = api.get_all_groups(client)
    emails = [u['email'] for u in result]

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
        'employee1@test.lyft.com',
        'employee2@test.lyft.com',
    ],
)
def test_sync_gsuite_users(all_users, load_gsuite_users, cleanup_gsuite_users):
    client = mock.MagicMock()
    gsuite_update_tag = 1
    session = mock.MagicMock()
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_users(session, client, gsuite_update_tag, common_job_param)
    users = all_users()
    load_gsuite_users.assert_called_with(
        session, users, gsuite_update_tag,
    )
    cleanup_gsuite_users.assert_called_once()


@patch('cartography.intel.gsuite.api.cleanup_gsuite_groups')
@patch('cartography.intel.gsuite.api.load_gsuite_groups')
@patch(
    'cartography.intel.gsuite.api.get_all_groups', return_value=[
        'group1@test.lyft.com',
        'group2@test.lyft.com',
    ],
)
def test_sync_gsuite_groups(all_groups, load_gsuite_groups, cleanup_gsuite_groups):
    client = mock.MagicMock()
    session = mock.MagicMock()
    gsuite_update_tag = 1
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_groups(session, client, gsuite_update_tag, common_job_param)
    groups = all_groups()
    load_gsuite_groups.assert_called_with(
        session, groups, gsuite_update_tag,
    )
    cleanup_gsuite_groups.assert_called_once()


def test_load_gsuite_groups():
    groups = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_groups(session, groups, update_tag)
    session.run.assert_called_with(
        api.get_ingestion_groups_qry(),
        UserData=groups,
        UpdateTag=update_tag,
    )


def test_load_gsuite_users():
    users = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_users(session, users, update_tag)
    session.run.assert_called_with(
        api.get_ingestion_users_qry(),
        UserData=users,
        UpdateTag=update_tag,
    )

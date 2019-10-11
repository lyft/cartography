from cartography.intel.okta.oktaintel import transform_okta_user
from tests.data.okta.users import create_test_user


def test_user_transform_with_all_values():
    user = create_test_user()

    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_activated():
    user = create_test_user()

    user.activated = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] is None
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_status_changed():
    user = create_test_user()

    user.statusChanged = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] is None
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_last_login():
    user = create_test_user()

    user.lastLogin = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] is None
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_last_updated():
    user = create_test_user()

    user.lastUpdated = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] is None
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_password_changed():
    user = create_test_user()

    user.passwordChanged = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] is None
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone


def test_userprofile_transform_with_no_transition_status():
    user = create_test_user()

    user.transitioningToStatus = None
    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == '01/01/2019, 00:00:01'
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["status_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["last_login"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'
    assert transform_props["password_changed"] == '01/01/2019, 00:00:01'
    assert transform_props["transition_to_status"] is None
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone

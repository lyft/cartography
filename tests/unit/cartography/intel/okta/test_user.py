from cartography.intel.okta.oktaintel import transform_okta_user
from tests.data.okta.users import create_test_user


def test_userprofile_transform_with_all_values():
    user = create_test_user()

    transform_props = transform_okta_user(user)

    assert transform_props["id"] == user.id
    assert transform_props["activated"] == user.activated
    assert transform_props["created"] == user.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["status_changed"] == user.statusChanged.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["last_login"] == user.lastLogin.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["okta_last_updated"] == user.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["password_changed"] == user.passwordChanged.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["transition_to_status"] == user.transitioningToStatus
    assert transform_props["login"] == user.profile.login
    assert transform_props["email"] == user.profile.email
    assert transform_props["second_email"] == user.profile.secondEmail
    assert transform_props["last_name"] == user.profile.lastName
    assert transform_props["first_name"] == user.profile.firstName
    assert transform_props["mobile_phone"] == user.profile.mobilePhone

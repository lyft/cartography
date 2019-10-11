from cartography.intel.okta.oktaintel import transform_group_roles_data
from cartography.intel.okta.oktaintel import transform_user_roles_data
from tests.data.okta.adminroles import LIST_ASSIGNED_GROUP_ROLE_RESPONSE
from tests.data.okta.adminroles import LIST_ASSIGNED_USER_ROLE_RESPONSE


def test_transform_user_roles():
    org_id = "example_org"
    props_list = transform_user_roles_data(LIST_ASSIGNED_USER_ROLE_RESPONSE, org_id)

    assert len(props_list) == 2
    assert props_list[0]["label"] == "Application Administrator"
    assert props_list[0]["type"] == "APP_ADMIN"
    assert props_list[0]["id"] == "example_org-APP_ADMIN"

    assert props_list[1]["label"] == "Help Desk Administrator"
    assert props_list[1]["type"] == "HELP_DESK_ADMIN"
    assert props_list[1]["id"] == "example_org-HELP_DESK_ADMIN"


def test_transform_group_roles():
    org_id = "example_org"
    props_list = transform_group_roles_data(LIST_ASSIGNED_GROUP_ROLE_RESPONSE, org_id)

    assert len(props_list) == 2
    assert props_list[0]["label"] == "Application Administrator"
    assert props_list[0]["type"] == "APP_ADMIN"
    assert props_list[0]["id"] == "example_org-APP_ADMIN"

    assert props_list[1]["label"] == "Help Desk Administrator"
    assert props_list[1]["type"] == "HELP_DESK_ADMIN"
    assert props_list[1]["id"] == "example_org-HELP_DESK_ADMIN"

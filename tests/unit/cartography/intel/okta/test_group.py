from cartography.intel.okta.groups import transform_okta_group
from cartography.intel.okta.groups import transform_okta_group_member
from tests.data.okta.groups import create_test_group
from tests.data.okta.groups import LIST_GROUP_MEMBER_RESPONSE


def test_group_transform_with_all_values():
    group = create_test_group()

    transform_props = transform_okta_group(group)

    assert transform_props["id"] == group.id
    assert transform_props["name"] == group.profile.name
    assert transform_props["description"] == group.profile.description
    assert transform_props["sam_account_name"] == group.profile.samAccountName
    assert transform_props["dn"] == group.profile.dn
    assert transform_props["windows_domain_qualified_name"] == group.profile.windowsDomainQualifiedName
    assert transform_props["external_id"] == group.profile.externalId


def test_group_transform_with_sam_account_none():
    group = create_test_group()

    group.profile.samAccountName = None
    transform_props = transform_okta_group(group)

    assert transform_props["id"] == group.id
    assert transform_props["name"] == group.profile.name
    assert transform_props["description"] == group.profile.description
    assert transform_props["sam_account_name"] is None
    assert transform_props["dn"] == group.profile.dn
    assert transform_props["windows_domain_qualified_name"] == group.profile.windowsDomainQualifiedName
    assert transform_props["external_id"] == group.profile.externalId


def test_group_transform_with_windows_domain_none():
    group = create_test_group()

    group.profile.windowsDomainQualifiedName = None
    transform_props = transform_okta_group(group)

    assert transform_props["id"] == group.id
    assert transform_props["name"] == group.profile.name
    assert transform_props["description"] == group.profile.description
    assert transform_props["sam_account_name"] == group.profile.samAccountName
    assert transform_props["dn"] == group.profile.dn
    assert transform_props["windows_domain_qualified_name"] is None
    assert transform_props["external_id"] == group.profile.externalId


def test_group_transform_with_external_id_none():
    group = create_test_group()

    group.profile.externalId = None
    transform_props = transform_okta_group(group)

    assert transform_props["id"] == group.id
    assert transform_props["name"] == group.profile.name
    assert transform_props["description"] == group.profile.description
    assert transform_props["sam_account_name"] == group.profile.samAccountName
    assert transform_props["dn"] == group.profile.dn
    assert transform_props["windows_domain_qualified_name"] == group.profile.windowsDomainQualifiedName
    assert transform_props["external_id"] is None


def test_group_member_list_transform():
    values_to_test = transform_okta_group_member(LIST_GROUP_MEMBER_RESPONSE)

    assert len(values_to_test) == 2
    assert values_to_test[0] == "00u1f96ECLNVOKVMUSEA"
    assert values_to_test[1] == "00u1f9cMYQZFMPVXIDIZ"

from cartography.intel.okta.oktaintel import transform_trusted_origins
from tests.data.okta.trustedorigin import LIST_TRUSTED_ORIGIN_RESPONSE


def test_transform_trusted_origin_all_values():
    prop_list = transform_trusted_origins(LIST_TRUSTED_ORIGIN_RESPONSE)

    assert len(prop_list) == 2

    current_props = prop_list[0]
    assert current_props["id"] == "tosue7JvguwJ7U6kz0g3"
    assert current_props["name"] == "Example Trusted Origin"
    assert current_props["origin"] == "http://example.com"
    assert len(current_props["scopes"]) == 1
    assert current_props["scopes"][0] == "CORS"
    assert current_props["status"] == "ACTIVE"
    assert current_props["created"] == "2018-01-13T01:22:10.000Z"
    assert current_props["created_by"] == "00ut5t92p6IEOi4bu0ge3"
    assert current_props["okta_last_updated"] == "2018-01-13T01:22:10.000Z"
    assert current_props["okta_last_updated_by"] == "00ut5t92p6IEOi4bu0g3"

    current_props = prop_list[1]
    assert current_props["id"] == "tos10hzarOl8zfPM80g4"
    assert current_props["name"] == "Another Trusted Origin"
    assert current_props["origin"] == "https://rf.example.com"
    assert len(current_props["scopes"]) == 2
    assert current_props["scopes"][0] == "CORS"
    assert current_props["scopes"][1] == "REDIRECT"
    assert current_props["status"] == "ACTIVE"
    assert current_props["created"] == "2017-11-16T05:01:12.000Z"
    assert current_props["created_by"] == "00ut5t92p6IEOi4bu10g31"
    assert current_props["okta_last_updated"] == "2017-12-16T05:01:12.000Z"
    assert current_props["okta_last_updated_by"] == "00ut5t92p6IEOi4bu0g34"

from cartography.intel.okta.applications import transform_application_assigned_groups
from cartography.intel.okta.applications import transform_application_assigned_users
from cartography.intel.okta.applications import transform_okta_application
from tests.data.okta.application import create_test_application
from tests.data.okta.application import LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE
from tests.data.okta.application import LIST_APPLICATION_USER_ASSIGNED_RESPONSE


def test_application_with_all_values():
    app = create_test_application()

    result = transform_okta_application(app)

    expected = {
        'id': app.id,
        'name': app.name,
        'label': app.label,
        'created': '01/01/2019, 00:00:01',
        'okta_last_updated': '01/01/2019, 00:00:01',
        'status': app.status,
        'activated': '01/01/2019, 00:00:01',
        'features': app.features,
        'sign_on_mode': app.signOnMode,
    }

    assert result == expected


def test_application_with_created_none():
    app = create_test_application()
    app.created = None

    result = transform_okta_application(app)

    expected = {
        'id': app.id,
        'name': app.name,
        'label': app.label,
        'created': None,
        'okta_last_updated': '01/01/2019, 00:00:01',
        'status': app.status,
        'activated': '01/01/2019, 00:00:01',
        'features': app.features,
        'sign_on_mode': app.signOnMode,
    }

    assert result == expected


def test_application_with_last_updated_none():
    app = create_test_application()
    app.lastUpdated = None

    result = transform_okta_application(app)

    expected = {
        'id': app.id,
        'name': app.name,
        'label': app.label,
        'created': '01/01/2019, 00:00:01',
        'okta_last_updated': None,
        'status': app.status,
        'activated': '01/01/2019, 00:00:01',
        'features': app.features,
        'sign_on_mode': app.signOnMode,
    }

    assert result == expected


def test_application_with_activated_none():
    app = create_test_application()
    app.activated = None

    result = transform_okta_application(app)

    expected = {
        'id': app.id,
        'name': app.name,
        'label': app.label,
        'created': '01/01/2019, 00:00:01',
        'okta_last_updated': '01/01/2019, 00:00:01',
        'status': app.status,
        'activated': None,
        'features': app.features,
        'sign_on_mode': app.signOnMode,
    }

    assert result == expected


def test_application_assigned_users():
    result = []

    result = transform_application_assigned_users(LIST_APPLICATION_USER_ASSIGNED_RESPONSE)

    expected = ["00ui2sVIFZNCNKFFNBPM", "00ujsgVNDRESKKXERBUJ"]
    assert result == expected


def test_application_assigned_groups():
    result = []

    result = transform_application_assigned_groups(LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE)

    expected = ["00gbkkGFFWZDLCNTAGQR", "00gg0xVALADWBPXOFZAS"]
    assert result == expected

from cartography.intel.okta.oktaintel import transform_application_users
from cartography.intel.okta.oktaintel import transform_applicationg_assigned_groups
from cartography.intel.okta.oktaintel import transform_okta_application
from tests.data.okta.application import create_test_application
from tests.data.okta.application import LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE
from tests.data.okta.application import LIST_APPLICATION_USER_ASSIGNED_RESPONSE


def test_application_with_all_values():
    app = create_test_application()

    transformed_data = transform_okta_application(app)

    assert transformed_data["id"] == app.id
    assert transformed_data["name"] == app.name
    assert transformed_data["label"] == app.label
    assert transformed_data["created"] == app.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["okta_last_updated"] == app.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["status"] == app.status
    assert transformed_data["activated"] == app.activated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["features"] == app.features
    assert transformed_data["sign_on_mode"] == app.signOnMode


def test_application_with_created_none():
    app = create_test_application()

    app.created = None
    transformed_data = transform_okta_application(app)

    assert transformed_data["id"] == app.id
    assert transformed_data["name"] == app.name
    assert transformed_data["label"] == app.label
    assert transformed_data["created"] is None
    assert transformed_data["okta_last_updated"] == app.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["status"] == app.status
    assert transformed_data["activated"] == app.activated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["features"] == app.features
    assert transformed_data["sign_on_mode"] == app.signOnMode


def test_application_with_last_updated_none():
    app = create_test_application()

    app.lastUpdated = None
    transformed_data = transform_okta_application(app)

    assert transformed_data["id"] == app.id
    assert transformed_data["name"] == app.name
    assert transformed_data["label"] == app.label
    assert transformed_data["created"] == app.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["okta_last_updated"] is None
    assert transformed_data["status"] == app.status
    assert transformed_data["activated"] == app.activated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["features"] == app.features
    assert transformed_data["sign_on_mode"] == app.signOnMode


def test_application_with_activated_none():
    app = create_test_application()
    app.activated = None

    transformed_data = transform_okta_application(app)

    assert transformed_data["id"] == app.id
    assert transformed_data["name"] == app.name
    assert transformed_data["label"] == app.label
    assert transformed_data["created"] == app.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["okta_last_updated"] == app.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    assert transformed_data["status"] == app.status
    assert transformed_data["activated"] is None
    assert transformed_data["features"] == app.features
    assert transformed_data["sign_on_mode"] == app.signOnMode


def test_application_assigned_users():
    values_to_test = []

    values_to_test.extend(transform_application_users(LIST_APPLICATION_USER_ASSIGNED_RESPONSE))

    assert len(values_to_test) == 2
    assert values_to_test[0] == "00ui2sVIFZNCNKFFNBPM"
    assert values_to_test[1] == "00ujsgVNDRESKKXERBUJ"


def test_application_assigned_groups():
    values_to_test = []

    values_to_test.extend(transform_applicationg_assigned_groups(LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE))

    assert len(values_to_test) == 2
    assert values_to_test[0] == "00gbkkGFFWZDLCNTAGQR"
    assert values_to_test[1] == "00gg0xVALADWBPXOFZAS"

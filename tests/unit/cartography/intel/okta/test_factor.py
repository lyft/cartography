from datetime import datetime
from tests.data.okta.userfactors import create_test_factor
from cartography.intel.okta.oktaintel import transform_okta_user_factor


def test_factor_transform_with_all_values():
    factor = create_test_factor()

    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] == factor.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["okta_last_updated"] == factor.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")


def test_factor_transform_with_created_none():
    factor = create_test_factor()

    factor.created = None
    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] == None
    assert transform_props["okta_last_updated"] == factor.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")


def test_factor_transform_with_lastupdated_none():
    factor = create_test_factor()

    factor.lastUpdated = None
    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] == factor.created.strftime("%m/%d/%Y, %H:%M:%S")
    assert transform_props["okta_last_updated"] == None



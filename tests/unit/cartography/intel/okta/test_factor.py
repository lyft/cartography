from cartography.intel.okta.factors import transform_okta_user_factor
from tests.data.okta.userfactors import create_test_factor


def test_factor_transform_with_all_values():
    factor = create_test_factor()

    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'


def test_factor_transform_with_created_none():
    factor = create_test_factor()

    factor.created = None
    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] is None
    assert transform_props["okta_last_updated"] == '01/01/2019, 00:00:01'


def test_factor_transform_with_lastupdated_none():
    factor = create_test_factor()

    factor.lastUpdated = None
    transform_props = transform_okta_user_factor(factor)

    assert transform_props["id"] == factor.id
    assert transform_props["factor_type"] == factor.factorType
    assert transform_props["provider"] == factor.provider
    assert transform_props["status"] == factor.status
    assert transform_props["created"] == '01/01/2019, 00:00:01'
    assert transform_props["okta_last_updated"] is None

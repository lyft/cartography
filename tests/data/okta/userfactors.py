import datetime

from okta.models.factor.Factor import Factor


def create_test_factor():
    factor = Factor()

    factor.id = "factor_id_value"
    factor.factorType = "factor_factorType_value"
    factor.provider = "factor_provider_value"
    factor.status = "factor_status_value"
    factor.created = datetime.datetime(2019, 1, 1, 0, 0, 1)
    factor.lastUpdated = datetime.datetime(2019, 1, 1, 0, 0, 1)

    return factor

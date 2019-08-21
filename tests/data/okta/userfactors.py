from datetime import datetime
from okta.models.factor.Factor import Factor


def create_test_factor():
    factor = Factor()

    factor.id = "jkljsdf"
    factor.factorType = "kljdslkfj"
    factor.provider = "lkjsdflkjsdf"
    factor.status = "sdf"
    factor.created = datetime.now()
    factor.lastUpdated = datetime.now()

    return factor

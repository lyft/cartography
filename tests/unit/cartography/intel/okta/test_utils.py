from cartography.intel.okta.utils import check_rate_limit
from tests.data.okta.utils import create_response
from tests.data.okta.utils import create_throttled_response


def test_utils_rate_limit_not_reached():
    response = create_response()

    result = check_rate_limit(response)

    expected = 0

    assert result == expected


def test_utils_rate_limit_reached():
    response = create_throttled_response()
    result = check_rate_limit(response)

    expected = 3

    assert result == expected

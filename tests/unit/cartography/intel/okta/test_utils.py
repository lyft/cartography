import time
from unittest import mock

import pytest

from cartography.intel.okta.utils import check_rate_limit
from tests.data.okta.utils import create_long_timeout_response
from tests.data.okta.utils import create_response
from tests.data.okta.utils import create_throttled_response


def test_utils_rate_limit_not_reached():
    response = create_response()

    result = check_rate_limit(response)

    expected = 0

    assert result == expected


@mock.patch.object(time, 'sleep', return_value=None)
def test_utils_rate_limit_reached(mock_sleep: mock.MagicMock):
    response = create_throttled_response()
    result = check_rate_limit(response)

    expected = 3

    assert result == expected
    mock_sleep.assert_called_once()


def test_utils_log_rate_limit_reset():
    response = create_long_timeout_response()

    with pytest.raises(Exception):
        check_rate_limit(response)

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import HTTPError

from cartography.intel.github.util import fetch_all


@patch('cartography.intel.github.util.fetch_page')
def test_fetch_all_handles_retries(mock_fetch_page: Mock) -> None:
    '''
    Ensures that fetch_all re-reaises the same exceptions when exceeding retry limit
    '''
    # Arrange
    exception = HTTPError
    response = Response()
    response.status_code = 500
    mock_fetch_page.side_effect = exception('my-error', response=response)
    retries = 3
    # Act
    with pytest.raises(exception) as excinfo:
        fetch_all('my-token', 'my-api_url', 'my-org', 'my-query', 'my-resource', retries=retries)
    # Assert
    mock_fetch_page.call_count == retries
    assert 'my-error' in str(excinfo.value)

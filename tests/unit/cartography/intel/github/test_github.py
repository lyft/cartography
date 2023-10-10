import typing
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone as tz
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from cartography.intel.github.util import _GRAPHQL_RATE_LIMIT_REMAINING_THREASHOLD
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import handle_rate_limit_sleep
from cartography.intel.github.util import inject_rate_limit_query
from tests.data.github.users import USERS_WITH_RATE_LIMIT_DATA
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


@patch('cartography.intel.github.util.fetch_page')
def test_fetch_all_handles_retries(mock_fetch_page: Mock) -> None:
    '''
    Ensures that fetch_all re-reaises the same exceptions when exceeding retry limit
    '''
    # Arrange
    exception = HTTPError
    mock_fetch_page.side_effect = exception('my-error')
    retries = 3
    # Act
    with pytest.raises(exception) as excinfo:
        fetch_all('my-token', 'my-api_url', 'my-org', '{my-query}', 'my-resource', retries=retries)
    # Assert
    assert mock_fetch_page.call_count == retries
    assert 'my-error' in str(excinfo.value)


@typing.no_type_check
@patch('cartography.intel.github.util.handle_rate_limit_sleep')
@patch('cartography.intel.github.util.inject_rate_limit_query')
@patch('cartography.intel.github.util.fetch_page')
def test_fetch_all(
    mock_fetch_page: Mock,
    mock_inject_rate_limit_query: Mock,
    mock_handle_rate_limit_sleep: Mock,
) -> None:
    '''
    Ensures that we inject the query string and do a sleep if necessary
    '''
    # Arrange
    token = 'my-token'
    api_url = 'my-api-url'
    org = 'my-org'
    resource_type = 'membersWithRole'
    original_query = '{my-query}'

    injected_query = '{my injected query}'
    mock_inject_rate_limit_query.return_value = injected_query

    end_cursor = USERS_WITH_RATE_LIMIT_DATA['data']['organization']['membersWithRole']['pageInfo']['endCursor']

    # above threshold
    resp_0 = deepcopy(USERS_WITH_RATE_LIMIT_DATA)
    resp_0['data']['organization']['membersWithRole']['pageInfo']['hasNextPage'] = True
    resp_0['data']['rateLimit']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THREASHOLD + 1

    # below threshold
    resp_1 = deepcopy(USERS_WITH_RATE_LIMIT_DATA)
    resp_1['data']['organization']['membersWithRole']['pageInfo']['hasNextPage'] = True
    resp_1['data']['rateLimit']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THREASHOLD - 1

    # finished
    resp_2 = deepcopy(USERS_WITH_RATE_LIMIT_DATA)
    resp_2['data']['organization']['membersWithRole']['pageInfo']['hasNextPage'] = False

    mock_fetch_page.side_effect = [
        resp_0,
        resp_1,
        resp_2,
    ]
    # Act
    fetch_all(token, api_url, org, original_query, resource_type)
    # Assert
    mock_inject_rate_limit_query.assert_called_once_with(original_query)
    # mock_sleep.assert_called_once_with()
    assert mock_fetch_page.call_args_list == [
        call(token, api_url, org, injected_query, None),
        call(token, api_url, org, injected_query, end_cursor),
        call(token, api_url, org, injected_query, end_cursor),
    ]
    assert mock_handle_rate_limit_sleep.call_args_list == [
        call(resp_0),
        call(resp_1),
        call(resp_2),
    ]


@typing.no_type_check
@patch('cartography.intel.github.util.time.sleep')
@patch('cartography.intel.github.util.datetime')
def test_handle_rate_limit_sleep(mock_datetime: Mock, mock_sleep: Mock) -> None:
    '''
    Ensures that handle_rate_limit_sleep sleeps when appropriate
    '''

    # Arrange
    mock_datetime.now = Mock(
        return_value=datetime(
            year=2040, month=1, day=1, hour=19, minute=0, second=0, tzinfo=tz.utc,
        ),
    )
    # +47 minutes
    reset_at = '2040-01-01T19:47:00Z'
    # sleep for one extra minute for safety
    expected_sleep_seconds = timedelta(minutes=48).seconds

    # above threshold
    resp_0 = deepcopy(USERS_WITH_RATE_LIMIT_DATA)
    resp_0['data']['organization']['membersWithRole']['pageInfo']['hasNextPage'] = True
    resp_0['data']['rateLimit']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THREASHOLD + 1
    resp_0['data']['rateLimit']['resetAt'] = reset_at

    # below threshold
    resp_1 = deepcopy(USERS_WITH_RATE_LIMIT_DATA)
    resp_1['data']['organization']['membersWithRole']['pageInfo']['hasNextPage'] = True
    resp_1['data']['rateLimit']['remaining'] = _GRAPHQL_RATE_LIMIT_REMAINING_THREASHOLD - 1
    resp_1['data']['rateLimit']['resetAt'] = reset_at

    # Act
    handle_rate_limit_sleep(resp_0)
    # Assert
    mock_datetime.now.assert_not_called()
    mock_sleep.assert_not_called()

    # Act
    mock_datetime.reset_mock()
    mock_sleep.reset_mock()
    handle_rate_limit_sleep(resp_1)
    # Assert
    mock_datetime.now.assert_called_once_with(tz.utc)
    mock_sleep.assert_called_once_with(expected_sleep_seconds)


def test_inject_rate_limit_query() -> None:
    '''
    Ensures that we inject the rateLimit sub-query properly
    '''
    # Arrange
    original_query = '''
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                login
                url
            }
        }
    '''
    expected = '''
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                login
                url
            }
            rateLimit {
                remaining
                resetAt
            }
        }
    '''
    # Act
    actual = inject_rate_limit_query(original_query)
    # Assert
    assert remove_leading_whitespace_and_empty_lines(expected) == remove_leading_whitespace_and_empty_lines(actual)

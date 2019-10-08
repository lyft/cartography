import pytest
from googleapiclient.discovery import HttpError
from unittest import mock
from cartography.intel.helper.google_request import repeat_request
from cartography.intel.helper.google_request import GoogleRetryException

def test_repeat_request():
    # Test pagination
    req = mock.MagicMock()
    req_args = {'lisa': 'sister', 'bart': 'brother'}
    req_next = mock.MagicMock()
    req_next.side_effect = [mock.MagicMock(), mock.MagicMock(), None]
    repeat_request(req, req_args, req_next, retry_delay_ms=1)
    assert req_next.call_count == 3

def test_repeat_request_fail():
    # Test that proper exception is raised on multiple retry failures
    req = mock.MagicMock()
    req_args = {'lisa': 'sister', 'bart': 'brother'}
    req(req_args).execute.side_effect = HttpError(resp=mock.MagicMock(), content=b'error')

    with pytest.raises(GoogleRetryException):
        repeat_request(req, req_args, req_next=None, retries=7, retry_delay_ms=1)
        assert req(req_args).execute.call_count == 7

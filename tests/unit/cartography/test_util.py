import pytest

from cartography import util
from cartography.util import aws_handle_regions
from cartography.util import botocore


def test_run_analysis_job_default_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with('cartography.data.jobs.analysis', 'test.json')


def test_run_analysis_job_custom_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock(), package='a.b.c')
    read_text_mock.assert_called_once_with('a.b.c', 'test.json')


def test_aws_handle_regions(mocker):
    # no exception
    @aws_handle_regions
    def happy_path(a, b):
        return a + b

    assert happy_path(1, 2) == 3

    # returns the default on_exception_return_value=[]
    @aws_handle_regions
    def raises_supported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'aws_handle_regions is not working',
                },
            },
            'FakeOperation',
        )
        raise e

    assert raises_supported_client_error(1, 2) == []

    # returns a custom value
    @aws_handle_regions(default_return_value=([], []))
    def raises_supported_error_with_custoim_return_value(a, b):
        e = botocore.exceptions.ClientError(
            {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'aws_handle_regions is not working',
                },
            },
            'FakeOperation',
        )
        raise e

    assert raises_supported_error_with_custoim_return_value(1, 2) == ([], [])

    # unhandled type of ClientError
    @aws_handle_regions
    def raises_unsupported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                'Error': {
                    'Code': '>9000',
                    'Message': 'aws_handle_regions is not working',
                },
            },
            'FakeOperation',
        )
        raise e

    with pytest.raises(botocore.exceptions.ClientError):
        raises_unsupported_client_error(1, 2)

    # other type of error besides ClientError
    @aws_handle_regions(default_return_value=9000)
    def raises_unsupported_error(a, b):
        return a / 0

    with pytest.raises(ZeroDivisionError):
        raises_unsupported_error(1, 2)

import logging
from unittest.mock import Mock

import boto3
import pytest
from botocore.stub import Stubber

from tests.data.aws.ecr import DESCRIBE_REPOSITORIES
from tests.data.aws.ecr import LIST_REPOSITORY_IMAGES


logging.basicConfig(level=logging.INFO)
logging.getLogger('botocore').setLevel(logging.WARNING)


DEFAULT_REGION = 'us-east-1'


@pytest.fixture
def boto3_session():
    '''
    Create a mock boto3 session that returns stubbed clients
    '''
    stubbed_clients = {
        DEFAULT_REGION: {
            service: make_stubbed_client(service, DEFAULT_REGION)
            for service in [
                'ecr',
            ]
        },
    }
    mock_boto3_session = Mock(
        client=Mock(
            side_effect=lambda service, region_name: stubbed_clients[region_name][service],
        ),
    )
    yield mock_boto3_session


def make_stubbed_client(service: str, region_name: str = DEFAULT_REGION):
    '''
    Create a boto3 client with stubbed responses
    '''
    client = boto3.client(service, region_name=region_name)
    stubber_funcs = {
        'ecr': stub_ecr,
    }
    stubber_funcs[service](client)
    return client


def stub_ecr(client: boto3.client) -> Stubber:
    '''
    Handle the stubbing of an ecr client
    '''
    stubber = Stubber(client)
    stubber.add_response("describe_repositories", DESCRIBE_REPOSITORIES)
    for repo_arn, image_list in LIST_REPOSITORY_IMAGES.items():
        repo_name = repo_arn.split("/", maxsplit=1)[-1]
        stubber.add_response(
            "list_images",
            {"imageIds": image_list},
            {"repositoryName": repo_name},
        )
    stubber.activate()
    return stubber

from typing import Callable
from typing import Dict
from unittest import mock

import cartography.config
import cartography.intel.aws
import cartography.util

# These unit tests are a sanity check for start*() and sync*() functions.

TEST_ACCOUNTS = {'profile1': '000000000000', 'profile2': '000000000001', 'profile3': '000000000002'}
TEST_REGIONS = ['us-east-1', 'us-west-2']
TEST_UPDATE_TAG = 123456789
GRAPH_JOB_PARAMETERS = {'UPDATE_TAG': TEST_UPDATE_TAG}

# Credit to https://stackoverflow.com/a/56687648 for the idea. Allows us to test the RESOURCE_FUNCTIONS table.
AWS_RESOURCE_FUNCTIONS_STUB: Dict[str, Callable] = {
    sync_name: mock.MagicMock() for sync_name in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.keys()
}


@mock.patch.object(cartography.intel.aws.organizations, 'sync', return_value=None)
@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch.object(cartography.intel.aws, '_sync_one_account', return_value=None)
@mock.patch.object(cartography.intel.aws, '_autodiscover_accounts', return_value=None)
@mock.patch.object(cartography.intel.aws, 'run_cleanup_job', return_value=None)
def test_sync_multiple_accounts(
    mock_cleanup, mock_autodiscover, mock_sync_one, mock_boto3_session, mock_sync_orgs, neo4j_session,
):
    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session, TEST_ACCOUNTS, TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )

    # Ensure we call _sync_one_account on all accounts in our list.
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000000', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
        aws_requested_syncs=[],
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000001', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
        aws_requested_syncs=[],
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000002', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
        aws_requested_syncs=[],
    )

    # Ensure _sync_one_account and _autodiscover is called once for each account
    assert mock_sync_one.call_count == len(TEST_ACCOUNTS.keys())
    assert mock_autodiscover.call_count == len(TEST_ACCOUNTS.keys())

    # This is a brittle test, but it is here to ensure that the mock_cleanup path is correct.
    assert mock_cleanup.call_count == 2


@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch('cartography.intel.aws.organizations')
@mock.patch.object(cartography.intel.aws, '_sync_multiple_accounts', return_value=None)
@mock.patch.object(cartography.intel.aws, 'run_analysis_job', return_value=None)
def test_start_aws_ingestion(mock_run_analysis, mock_sync_multiple, mock_orgs, mock_boto3, neo4j_session):
    test_config = cartography.config.Config(
        neo4j_uri='bolt://localhost:7687',
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
    )
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)
    assert mock_sync_multiple.call_count == 1

    # Brittle, but here to ensure that our mock_run_analysis path is correct.
    assert mock_run_analysis.call_count == 3


def test_my_dumb_test():
    a = {'a': 1, 'b': 3, 'c': 3}
    from unittest.mock import MagicMock
    m = MagicMock()
    m(a=1, b=3, c=2, d=5)
    assert m.call_count == 1
    assert m.called_with(**a)


@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch.dict('cartography.intel.aws.RESOURCE_FUNCTIONS', AWS_RESOURCE_FUNCTIONS_STUB)
@mock.patch.object(cartography.intel.aws.resourcegroupstaggingapi, 'sync', return_value=None)
@mock.patch('cartography.intel.aws.permission_relationships.sync')
@mock.patch.object(cartography.intel.aws, '_autodiscover_account_regions', return_value=TEST_REGIONS)
@mock.patch.object(cartography.intel.aws, 'run_cleanup_job', return_value=None)
def test_sync_one_account_all_functions(
    mock_cleanup, mock_autodiscover, mock_perm_rels, mock_tags, mock_boto3_session, neo4j_session,
):
    aws_sync_test_kwargs = {
        'neo4j_session': neo4j_session,
        'boto3_session': mock_boto3_session(),
        'current_aws_account_id': '1234',
        'update_tag': TEST_UPDATE_TAG,
        'common_job_parameters': GRAPH_JOB_PARAMETERS,
    }
    cartography.intel.aws._sync_one_account(
        **aws_sync_test_kwargs,
    )
    # Check that the boilerplate functions get called as expected. Brittle, but a good sanity check. Update accordingly.
    assert mock_autodiscover.call_count == 1
    assert mock_cleanup.call_count == 1

    # Test that ALL syncs got called.
    # TODO i'm not sure how to get .called_with() working in this function table, so I am creating a separate test.
    for sync_name in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.keys():
        print(sync_name)
        if sync_name not in ['permission_relationships', 'resourcegroupstaggingapi']:
            assert AWS_RESOURCE_FUNCTIONS_STUB[sync_name].call_count == 1
    assert mock_perm_rels.called_with(**aws_sync_test_kwargs)
    assert mock_tags.called_with(**aws_sync_test_kwargs)


@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch.dict('cartography.intel.aws.RESOURCE_FUNCTIONS', AWS_RESOURCE_FUNCTIONS_STUB)
@mock.patch.object(cartography.intel.aws.resourcegroupstaggingapi, 'sync', return_value=None)
@mock.patch('cartography.intel.aws.permission_relationships.sync')
@mock.patch.object(cartography.intel.aws, '_autodiscover_account_regions', return_value=TEST_REGIONS)
@mock.patch.object(cartography.intel.aws, 'run_cleanup_job', return_value=None)
def test_sync_one_account_subset(
    mock_cleanup, mock_autodiscover, mock_perm_rels, mock_tags, mock_boto3_session, neo4j_session,
):
    cartography.intel.aws._sync_one_account(
        neo4j_session, mock_boto3_session(), '1234', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
        aws_requested_syncs=['iam', 'permission_relationships', 'resourcegroupstaggingapi'],
    )

    # Test that the syncs we requested (IAM, perm rels, tags) actually got called.
    assert AWS_RESOURCE_FUNCTIONS_STUB['iam'].called_with(
        neo4j_session, mock_boto3_session(), [], '1234', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )
    assert mock_perm_rels.call_count == 1
    assert mock_tags.call_count == 1

    # Check that the boilerplate functions get called as expected. Brittle, but a good sanity check.
    assert mock_autodiscover.call_count == 1
    assert mock_cleanup.call_count == 1

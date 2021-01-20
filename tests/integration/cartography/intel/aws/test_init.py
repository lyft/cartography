from unittest import mock

import cartography.config
import cartography.intel.aws
import cartography.util

# These unit tests are a sanity check for start*() and sync*() functions.

TEST_ACCOUNTS = {'profile1': '000000000000', 'profile2': '000000000001', 'profile3': '000000000002'}
TEST_REGIONS = ['us-east-1', 'us-west-2']
TEST_UPDATE_TAG = 123456789
GRAPH_JOB_PARAMETERS = {'UPDATE_TAG': TEST_UPDATE_TAG}


@mock.patch.object(cartography.intel.aws.organizations, 'sync', return_value=None)
@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch.object(cartography.intel.aws, '_sync_one_account', return_value=None)
@mock.patch.object(cartography.intel.aws, '_autodiscover_accounts', return_value=None)
@mock.patch.object(cartography.util, 'run_cleanup_job', return_value=None)
def test_sync_multiple_accounts(
    mock_cleanup, mock_autodiscover, mock_sync_one, mock_boto3_session, mock_sync_orgs, neo4j_session,
):
    cartography.intel.aws._sync_multiple_accounts(neo4j_session, TEST_ACCOUNTS, TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS)

    # Ensure we call _sync_one_account on all accounts in our list.
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000000', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000001', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_boto3_session(), '000000000002', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )

    # Ensure _sync_one_account and _autodiscover is called once for each account
    assert mock_sync_one.call_count == len(TEST_ACCOUNTS.keys())
    assert mock_autodiscover.call_count == len(TEST_ACCOUNTS.keys())


@mock.patch('cartography.intel.aws.boto3.Session')
@mock.patch('cartography.intel.aws.organizations')
@mock.patch.object(cartography.intel.aws, '_sync_multiple_accounts', return_value=None)
@mock.patch.object(cartography.util, 'run_analysis_job', return_value=None)
def test_start_aws_ingestion(mock_run_analysis, mock_sync_multiple, mock_orgs, mock_boto3, neo4j_session):
    test_config = cartography.config.Config(
        neo4j_uri='bolt://localhost:7687',
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
    )
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)
    assert mock_sync_multiple.call_count == 1

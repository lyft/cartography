import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from unittest import mock

import neo4j

import cartography.config
import cartography.intel.azure
import cartography.util

# These unit tests are a sanity check for start*() and sync*() functions.

TEST_SUBSCRIPTIONS = [
    {
        "id": "000000",
        "subscriptionId": "000000",
        "displayName": "profile",
        "state": "active"
    },
    {
        "id": "000001",
        "subscriptionId": "000001",
        "displayName": "profile1",
        "state": "active"
    }
]
TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = '000000'
GRAPH_JOB_PARAMETERS = {'UPDATE_TAG': TEST_UPDATE_TAG}


@mock.patch('azure.util.credentials.Credentials')
@mock.patch.object(cartography.intel.azure, '_sync_one_subscription', return_value=None)
# @mock.patch.object(cartography.intel.azure, '_sync_tenant', return_value=None)
@mock.patch.object(cartography.util, 'run_cleanup_job', return_value=None)
def test_sync_multiple_subscriptions(
        mock_cleanup, mock_sync_one, mock_credentials, neo4j_session,
):
    cartography.intel.azure._sync_multiple_subscriptions(
        neo4j_session, mock_credentials, TEST_TENANT_ID, TEST_SUBSCRIPTIONS, TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS)

    # Ensure we call _sync_one_account on all accounts in our list.
    mock_sync_one.assert_any_call(
        neo4j_session, mock_credentials, '00-00-00-00', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_credentials, '00-00-00-01', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )
    mock_sync_one.assert_any_call(
        neo4j_session, mock_credentials, '00-00-00-02', TEST_UPDATE_TAG, GRAPH_JOB_PARAMETERS,
    )

    # Ensure _sync_one_account and _autodiscover is called once for each account
    assert mock_sync_one.call_count == len(TEST_SUBSCRIPTIONS)


@mock.patch.object(cartography.intel.azure, '_sync_multiple_subscriptions', return_value=None)
@mock.patch.object(cartography.util, 'run_analysis_job', return_value=None)
def test_start_azure_ingestion(mock_run_analysis, mock_sync_multiple, neo4j_session):
    test_config = cartography.config.Config(
        neo4j_uri='bolt://localhost:7687',
        update_tag=TEST_UPDATE_TAG,
        azure_sync_all_subscriptions=True,
    )
    cartography.intel.azure.start_azure_ingestion(neo4j_session, test_config)
    assert mock_sync_multiple.call_count == 1

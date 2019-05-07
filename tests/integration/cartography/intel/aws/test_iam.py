import neo4j
import pytest

import cartography.intel.aws.iam
import tests.data.aws.iam


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_roles(neo4j_session):
    data = tests.data.aws.iam.LIST_ROLES['Roles']

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )

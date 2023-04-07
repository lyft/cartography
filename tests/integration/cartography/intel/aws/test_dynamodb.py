from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.aws.dynamodb, 'get_dynamodb_tables', return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES['Tables'])
def test_load_dynamodb(mock_get_instances, neo4j_session):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()

    # Act
    cartography.intel.aws.dynamodb.sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert ddb table nodes exist
    assert check_nodes(neo4j_session, 'DynamoDBTable', ['id', 'rows']) == {
        ("arn:aws:dynamodb:us-east-1:000000000000:table/example-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/sample-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/model-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/basic-table", 1000000),
    }

    # Assert ddb gsi nodes exist
    assert check_nodes(neo4j_session, 'DynamoDBGlobalSecondaryIndex', ['id']) == {
        ('arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index',),
    }

    # Assert DynamoDBTable -> DynamoDBGlobalSecondaryIndex
    assert check_rels(
        neo4j_session,
        'DynamoDBTable',
        'id',
        'DynamoDBGlobalSecondaryIndex',
        'id',
        'GLOBAL_SECONDARY_INDEX',
        rel_direction_right=True,
    ) == {
        ('arn:aws:dynamodb:us-east-1:000000000000:table/example-table',
        'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/example-table',
        'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
        'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
        'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
        'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
        'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
        'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
        'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index'),
    }
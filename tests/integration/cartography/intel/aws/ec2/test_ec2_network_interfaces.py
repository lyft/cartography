from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.network_interfaces
from cartography.intel.aws.ec2.network_interfaces import sync_network_interfaces
from tests.data.aws.ec2.network_interfaces import DESCRIBE_NETWORK_INTERFACES
from tests.integration.cartography.intel.aws.common import create_test_account

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-north-1'
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.network_interfaces,
    'get_network_interface_data',
    return_value=DESCRIBE_NETWORK_INTERFACES,
)
def test_load_network_interfaces(mock_get_network_interfaces, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_network_interfaces(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert 1
    expected_nodes = {
        "eni-0e106a07c15ff7d14",
        "eni-0d9877f559c240362",
        "eni-04b4289e1be7634e4",
    }

    nodes = neo4j_session.run(
        """
        MATCH (ni:NetworkInterface) RETURN ni.id;
        """,
    )
    actual_nodes = {n['ni.id'] for n in nodes}

    assert actual_nodes == expected_nodes

    # TODO use test helpers

    # Assert 2
    expected_nodes = {
        "eni-0e106a07c15ff7d14:10.0.4.180",
        "eni-0d9877f559c240362:10.0.4.96",
        "eni-04b4289e1be7634e4:10.0.4.5",
        "eni-04b4289e1be7634e4:10.0.4.12",
    }

    nodes = neo4j_session.run(
        """
        MATCH (ni:EC2PrivateIp) RETURN ni.id;
        """,
    )
    actual_nodes = {n['ni.id'] for n in nodes}

    assert actual_nodes == expected_nodes

    # Assert 3
    expected_nodes = {
        ('eni-0e106a07c15ff7d14', 'eni-0e106a07c15ff7d14:10.0.4.180'),
        ('eni-0d9877f559c240362', 'eni-0d9877f559c240362:10.0.4.96'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.5'),
        ('eni-04b4289e1be7634e4', 'eni-04b4289e1be7634e4:10.0.4.12'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:NetworkInterface)-[:PRIVATE_IP_ADDRESS]->(n2:EC2PrivateIp) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected_nodes

    # Assert 4
    expected_nodes = {
        ('eni-0e106a07c15ff7d14', TEST_ACCOUNT_ID),
        ('eni-0d9877f559c240362', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
        ('eni-04b4289e1be7634e4', TEST_ACCOUNT_ID),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:NetworkInterface)<-[:RESOURCE]-(n2:AWSAccount) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected_nodes

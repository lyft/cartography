import cartography.intel.aws.emr
import tests.data.aws.emr
from cartography.intel.aws.emr import cleanup
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _create_test_accounts(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )


def test_load_emr_clusters_nodes(neo4j_session):
    # Act
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",),
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",),
    }
    assert check_nodes(neo4j_session, 'EMRCluster', ['arn']) == expected_nodes


def test_load_emr_clusters_relationships(neo4j_session):
    _create_test_accounts(neo4j_session)

    # Act: Load Test EMR Clusters
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected = {
        (TEST_ACCOUNT_ID, 'arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome'),
        (TEST_ACCOUNT_ID, 'arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh'),
    }
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'EMRCluster',
        'arn',
        'RESOURCE',
    ) == expected


def test_cleanup_emr(neo4j_session):
    # Arrange: load EMR cluster data
    data = tests.data.aws.emr.DESCRIBE_CLUSTERS
    _create_test_accounts(neo4j_session)
    cartography.intel.aws.emr.load_emr_clusters(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Setup: assert that data is in the graph
    expected_nodes = {
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-awesome",),
        ("arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/j-meh",),
    }
    assert check_nodes(neo4j_session, 'EMRCluster', ['arn']) == expected_nodes

    # Act: run the cleanup job
    cleanup(
        neo4j_session,
        {
            'UPDATE_TAG': TEST_UPDATE_TAG + 1,  # Simulate that is a new sync run so the prev update tag is obsolete now
            'AccountId': TEST_ACCOUNT_ID,
        },
    )

    # Assert: Expect no EMR clusters in the graph now
    assert check_nodes(neo4j_session, 'EMRCluster', ['arn']) == set()

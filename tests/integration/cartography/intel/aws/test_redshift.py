import cartography.intel.aws.ec2.security_groups
import cartography.intel.aws.redshift
import tests.data.aws.ec2.security_groups
import tests.data.aws.redshift
from cartography.util import run_analysis_job

TEST_ACCOUNT_ID = '1111'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '1234'


def test_load_redshift_cluster_data(neo4j_session):
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that the Redshift cluster node was created
    expected_nodes = {
        "arn:aws:redshift:us-east-1:1111:cluster:my-cluster",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:RedshiftCluster) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_redshift_redshift_reserved_node_data(neo4j_session):
    _ensure_local_neo4j_has_test_redshift_reserved_node_data(neo4j_session)
    expected_nodes = {
        "arn:aws:redshift:us-east-1:1111:reserved-node/1ba8e2e3-bc01-4d65-b35d-a4a3e931547e",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:RedshiftReservedNode) RETURN n.id;
        """,
    )
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_redshift_cluster_and_aws_account(neo4j_session):
    # Create test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that AWSAccount-to-RedshiftCluster relationships exist
    expected = {
        (TEST_ACCOUNT_ID, 'arn:aws:redshift:us-east-1:1111:cluster:my-cluster'),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected


def test_load_redshift_cluster_and_security_group(neo4j_session):
    # Create test EC2 security group
    neo4j_session.run(
        """
        MERGE (aws:EC2SecurityGroup{id: $GroupId})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        GroupId='sg-028e2522c72719996',
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-EC2SecurityGroup relationships exist
    expected = {
        ('sg-028e2522c72719996', 'arn:aws:redshift:us-east-1:1111:cluster:my-cluster'),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected


def test_load_redshift_cluster_and_iam_role(neo4j_session):
    # Create test IAM role
    neo4j_session.run(
        """
        MERGE (aws:AWSPrincipal:AWSRole{arn: $RoleArn})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        RoleArn='arn:aws:iam::1111:role/my-test-role',
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-IAM-role relationships exist
    expected = {
        ('arn:aws:iam::1111:role/my-redshift-iam-role', 'arn:aws:redshift:us-east-1:1111:cluster:my-cluster'),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSPrincipal)<-[:STS_ASSUMEROLE_ALLOW]-(n2:RedshiftCluster) RETURN n1.arn, n2.id;
        """,
    )
    actual = {
        (r['n1.arn'], r['n2.id']) for r in result
    }
    assert actual == expected


def test_load_redshift_cluster_and_vpc(neo4j_session):
    # Create test VPC
    neo4j_session.run(
        """
        MERGE (aws:AWSVpc{id: $VpcId})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        VpcId='my_vpc',
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-VPC relationships exist
    expected = {
        ('my_vpc', 'arn:aws:redshift:us-east-1:1111:cluster:my-cluster'),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSVpc)<-[:MEMBER_OF_AWS_VPC]-(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected


def _ensure_local_neo4j_has_test_cluster_data(neo4j_session):
    """Pre-load the Neo4j instance with sample Redshift data"""
    clusters = tests.data.aws.redshift.CLUSTERS
    cartography.intel.aws.redshift.transform_redshift_cluster_data(
        clusters,
        TEST_ACCOUNT_ID,
    )
    cartography.intel.aws.redshift.load_redshift_cluster_data(
        neo4j_session,
        clusters,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_redshift_reserved_node_data(neo4j_session):
    nodes = tests.data.aws.redshift.NODES
    cartography.intel.aws.redshift.load_redshift_reserved_node(
        neo4j_session,
        nodes,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_redshift_cluster_analysis(neo4j_session):
    neo4j_session.run(
        """
            MERGE (aws:AWSAccount{id: $aws_account_id})<-[:OWNER]-(:CloudanixWorkspace{id: $workspace_id})
            ON CREATE SET aws.firstseen = timestamp()
            SET aws.lastupdated = $aws_update_tag
            """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
        workspace_id=TEST_WORKSPACE_ID,
    )

    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    run_analysis_job(
        'aws_redshift_cluster_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    nodes = neo4j_session.run(
        """
        MATCH (n:RedshiftCluster{exposed_internet: true}) return n.id, n.exposed_internet_type;
        """,
    )

    actual_nodes = {(n['n.id'], ",".join(n['n.exposed_internet_type'])) for n in nodes}

    expected_nodes = {
        ('arn:aws:redshift:us-east-1:1111:cluster:my-cluster', 'direct_ipv4'),
    }

    assert actual_nodes == expected_nodes

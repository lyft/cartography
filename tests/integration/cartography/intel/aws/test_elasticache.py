import cartography.intel.aws.ec2.security_groups
import cartography.intel.aws.elasticache
import tests.data.aws.ec2.security_groups
import tests.data.aws.elasticache
from cartography.util import run_analysis_job

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '12345'


def test_load_clusters(neo4j_session):
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
    elasticache_data = tests.data.aws.elasticache.DESCRIBE_CACHE_CLUSTERS
    clusters = elasticache_data['CacheClusters']
    cartography.intel.aws.elasticache.load_elasticache_clusters(
        neo4j_session,
        clusters,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_cluster_arns = {cluster['ARN'] for cluster in clusters}
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheCluster) RETURN r.arn
        """,
    )
    actual_cluster_arns = {n['r.arn'] for n in nodes}
    assert actual_cluster_arns == expected_cluster_arns

    # Test the connection to the account
    expected_cluster_arns = {(cluster['ARN'], TEST_ACCOUNT_ID) for cluster in clusters}
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheCluster)<-[:RESOURCE]-(a:AWSAccount) RETURN r.arn, a.id
        """,
    )
    actual_cluster_arns = {(n['r.arn'], n['a.id']) for n in nodes}
    assert actual_cluster_arns == expected_cluster_arns

    # Test undefined topic_arns
    topic_arns_in_test_data = {cluster.get('NotificationConfiguration', {}).get('TopicArn') for cluster in clusters}
    expected_topic_arns = {topic for topic in topic_arns_in_test_data if topic}  # Filter out Nones.
    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheTopic) RETURN r.arn
        """,
    )
    actual_topic_arns = {n['r.arn'] for n in nodes}
    assert actual_topic_arns == expected_topic_arns


def test_elasticache_cluster_analysis(neo4j_session):
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

    elasticache_data = tests.data.aws.elasticache.DESCRIBE_CACHE_CLUSTERS
    clusters = elasticache_data['CacheClusters']
    cartography.intel.aws.elasticache.load_elasticache_clusters(
        neo4j_session,
        clusters,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.elasticache.attach_elasticache_clusters_to_security_groups(neo4j_session, clusters, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    run_analysis_job(
        'aws_elasticache_cluster_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    nodes = neo4j_session.run(
        """
        MATCH (r:ElasticacheCluster{exposed_internet: true}) RETURN r.arn, r.exposed_internet_type
        """,
    )
    actual_nodes = {(n['r.arn'], ",".join(n['r.exposed_internet_type'])) for n in nodes}

    expected_nodes = {('arn:aws:elasticache:us-east-1:123456789000:cluster:test-group-0001-001', 'direct_ipv4')}
    assert actual_nodes == expected_nodes

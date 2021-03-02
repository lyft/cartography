import logging

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_topic(cluster):
    return cluster['NotificationConfiguration']


def transform_elasticache_topics(cluster_data):
    """
    Collect unique TopicArns from the cluster data
    """
    seen = set()
    topics = []
    for cluster in cluster_data:
        topic = _get_topic(cluster)
        topic_arn = topic['TopicArn']
        if topic_arn not in seen:
            seen.add(topic_arn)
            topics.append(topic)
    return topics


@timeit
@aws_handle_regions
def get_elasticache_clusters(boto3_session, region):
    logger.debug(f"Getting ElastiCache Clusters in region '{region}'.")
    client = boto3_session.client('elasticache', region_name=region)
    paginator = client.get_paginator('describe_cache_clusters')
    clusters = []
    for page in paginator.paginate():
        clusters.extend(page['CacheClusters'])
    return clusters


@timeit
def load_elasticache_clusters(neo4j_session, clusters, region, aws_account_id, update_tag):
    query = """
    UNWIND {clusters} as elasticache_cluster
        MERGE (cluster:ElasticacheCluster{id:elasticache_cluster.ARN})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = elasticache_cluster.ARN,
            cluster.topic_arn = elasticache_cluster.NotificationConfiguration.TopicArn,
            cluster.id = elasticache_cluster.CacheClusterId,
            cluster.region = {region}
        SET cluster.lastupdated = {aws_update_tag}

        MERGE (topic:ElasticacheTopic{id: elasticache_cluster.NotificationConfiguration.TopicArn})
        ON CREATE SET topic.firstseen = timestamp(),
            topic.arn = elasticache_cluster.NotificationConfiguration.TopicArn
        SET topic.lastupdated = {aws_update_tag},
            topic.status = elasticache_cluster.NotificationConfiguration.Status

        MERGE (topic)-[r:CACHE_CLUSTER]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        WITH cluster, topic

        MATCH (owner:AWSAccount{id: {aws_account_id}})
        MERGE (owner)-[r2:RESOURCE]->(topic)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = {aws_update_tag}
        MERGE (owner)-[r3:RESOURCE]->(cluster)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = {aws_update_tag}
    """
    logger.info(f"Loading f{len(clusters)} ElastiCache clusters for region '{region}' into graph.")
    neo4j_session.run(
        query,
        clusters=clusters,
        region=region,
        aws_update_tag=update_tag,
        aws_account_id=aws_account_id,
    )


@timeit
def cleanup(neo4j_session, current_aws_account_id, update_tag):
    run_cleanup_job(
        'aws_import_elasticache_cleanup.json',
        neo4j_session,
        {'UPDATE_TAG': update_tag, 'AWS_ID': current_aws_account_id},
    )


@timeit
def sync(neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters):
    for region in regions:
        logger.info(f"Syncing ElastiCache clusters for region '{region}' in account {current_aws_account_id}")
        clusters = get_elasticache_clusters(boto3_session, region)
        load_elasticache_clusters(neo4j_session, clusters, region, current_aws_account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)

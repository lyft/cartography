import logging
from typing import Dict
from typing import List

from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_emr_clusters(boto3_session, region) -> List[Dict]:
    client = boto3_session.client('emr', region_name=region)
    clusters: List[Dict] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator:
        cluster = page['Clusters']
        clusters.extend(cluster)
        print(cluster['Id'])
    return clusters

@timeit
def load_emr_clusters(neo4j_session, cluster_data, region, current_aws_account_id, aws_update_tag):
    query = """
    UNWIND {Clusters} as emr_cluster
        MERGE (cluster:EMRCluster{id: emr_cluster.Name})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.name = emr_cluster.Name,
            cluster.region = {Region}
        SET cluster.lastupdated = {aws_update_tag}
        WITH cluster

        MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (owner)-[r:RESOURCE]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    logger.debug("Loading EMR clusters for region '%s' into graph.", region)
    neo4j_session.run(
        query,
        Clusters=cluster_data,
        Region=region,
        aws_update_tag=aws_update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    ).consume()

@timeit
def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing EMR for region '%s' in account '%s'.", reggion, current_aws_account_id)
        
        clusters = get_emr_clusters(boto3_session, region)

import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_eks_clusters(boto3_session, region):
    client = boto3_session.client('eks', region_name=region)
    clusters = []
    paginator = client.get_paginator('list_clusters')
    try:
        for page in paginator.paginate():
            clusters.extend(page['clusters'])
    except client.exceptions.ClientError as e:
        # The account is not authorized to use this service in this region
        # so we can continue without raising an exception
        if e.response['Error']['Code'] == 'AccessDeniedException' \
                and 'not authorized to use this service' in e.response['Error']['Message']:
            logger.warn("{} in this region. Skipping...".format(e.response['Error']['Message']))
        else:
            raise
    return clusters


def get_eks_describe_cluster(boto3_session, region, cluster_name):
    client = boto3_session.client('eks', region_name=region)
    response = client.describe_cluster(name=cluster_name)
    return response['cluster']


def load_eks_clusters(neo4j_session, cluster_data, region, current_aws_account_id, aws_update_tag):
    query = """
    MERGE (cluster:EKSCluster{id: {ClusterArn}})
    ON CREATE SET cluster.firstseen = timestamp(),
                cluster.arn = {ClusterArn},
                cluster.name = {ClusterName},
                cluster.region = {Region},
                cluster.created_at = {CreatedAt}
    SET cluster.lastupdated = {aws_update_tag},
        cluster.endpoint = {ClusterEndpoint},
        cluster.version = {ClusterVersion},
        cluster.platform_version = {ClusterPlatformVersion},
        cluster.status = {ClusterStatus}
    WITH cluster
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(cluster)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for cd in cluster_data:
        cluster = cluster_data[cd]
        neo4j_session.run(
            query,
            ClusterArn=cluster['arn'],
            ClusterName=cluster['name'],
            ClusterEndpoint=cluster['endpoint'],
            ClusterVersion=cluster['version'],
            ClusterPlatformVersion=cluster['platformVersion'],
            ClusterStatus=cluster['status'],
            CreatedAt=str(cluster['createdAt']),
            Region=region,
            aws_update_tag=aws_update_tag,
            AWS_ACCOUNT_ID=current_aws_account_id,
        )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_eks_cleanup.json', neo4j_session, common_job_parameters)


def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing EKS for region '%s' in account '%s'.", region, current_aws_account_id)

        clusters = get_eks_clusters(boto3_session, region)

        cluster_data = {}
        for cluster_name in clusters:
            cluster_data[cluster_name] = get_eks_describe_cluster(boto3_session, region, cluster_name)

        load_eks_clusters(neo4j_session, cluster_data, region, current_aws_account_id, aws_update_tag)

    cleanup(neo4j_session, common_job_parameters)

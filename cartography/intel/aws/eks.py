import time
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('eks', region_name=region)
    clusters: List[Dict] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        clusters.extend(page['clusters'])
    clusters_data = []
    for cluster in clusters:
        cluster_data = {}
        cluster_data['name'] = cluster
        cluster_data['region'] = region
        # clusters_data['consolelink'] = aws_console_link.get_console_link(arn=clusters_data['arn'])
        clusters_data.append(cluster_data)
    return clusters_data


@timeit
def get_eks_describe_cluster(boto3_session: boto3.session.Session, region: str, cluster_name: str) -> Dict:
    client = boto3_session.client('eks', region_name=region)
    response = client.describe_cluster(name=cluster_name)
    response['cluster']['region'] = region
    response['cluster']['arn'] = aws_console_link.get_console_link(arn=response['cluster']['arn'])
    return response['cluster']


@timeit
def load_eks_clusters(
    neo4j_session: neo4j.Session, cluster_data: Dict, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    MERGE (cluster:EKSCluster{id: {ClusterArn}})
    ON CREATE SET cluster.firstseen = timestamp(),
                cluster.arn = {ClusterArn},
                cluster.name = {ClusterName},
                cluster.consolelink = {consolelink},
                cluster.region = {Region},
                cluster.created_at = {CreatedAt}
    SET cluster.lastupdated = {aws_update_tag},
        cluster.endpoint = {ClusterEndpoint},
        cluster.endpoint_public_access = {ClusterEndointPublic},
        cluster.rolearn = {ClusterRoleArn},
        cluster.version = {ClusterVersion},
        cluster.platform_version = {ClusterPlatformVersion},
        cluster.status = {ClusterStatus},
        cluster.audit_logging = {ClusterLogging}
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
            consolelink=cluster.get('consolelink'),
            ClusterEndpoint=cluster.get('endpoint'),
            ClusterEndointPublic=cluster.get('resourcesVpcConfig', {}).get('endpointPublicAccess'),
            ClusterRoleArn=cluster.get('roleArn'),
            ClusterVersion=cluster.get('version'),
            ClusterPlatformVersion=cluster.get('platformVersion'),
            ClusterStatus=cluster.get('status'),
            CreatedAt=str(cluster.get('createdAt')),
            ClusterLogging=_process_logging(cluster),
            Region=cluster['region'],
            aws_update_tag=aws_update_tag,
            AWS_ACCOUNT_ID=current_aws_account_id,
        )


def _process_logging(cluster: Dict) -> bool:
    """
    Parse cluster.logging.clusterLogging to verify if
    at least one entry has audit logging set to Enabled.
    """
    logging: bool = False
    cluster_logging: Any = cluster.get('logging', {}).get('clusterLogging')
    if cluster_logging:
        logging = any(filter(lambda x: 'audit' in x['types'] and x['enabled'], cluster_logging))  # type: ignore
    return logging


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_eks_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EKS for account '%s', at %s.", current_aws_account_id, tic)

    clusters = []
    for region in regions:
        logger.info("Syncing EKS for region '%s' in account '%s'.", region, current_aws_account_id)

        clusters.extend(get_eks_clusters(boto3_session, region))

    if common_job_parameters.get('pagination', {}).get('eks', None):
        pageNo = common_job_parameters.get("pagination", {}).get("eks", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("eks", None)["pageSize"]
        totalPages = len(clusters) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for eks clusters {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('eks', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('eks', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('eks', {})['pageSize']
        if page_end > len(clusters) or page_end == len(clusters):
            clusters = clusters[page_start:]
        else:
            has_next_page = True
            clusters = clusters[page_start:page_end]
            common_job_parameters['pagination']['eks']['hasNextPage'] = has_next_page

    cluster_data: Dict = {}
    for cluster in clusters:
        cluster_data[cluster['name']] = get_eks_describe_cluster(boto3_session, cluster['region'], cluster['name'])

    load_eks_clusters(neo4j_session, cluster_data, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Total Time to process EKS: {toc - tic:0.4f} seconds")

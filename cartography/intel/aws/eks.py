import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
import uuid

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.eks.clusters import EKSClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = boto3_session.client('eks', region_name=region)
    clusters: List[str] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        clusters.extend(page['clusters'])
    return clusters


@timeit
def get_eks_describe_cluster(boto3_session: boto3.session.Session, region: str, cluster_name: str) -> Dict:
    client = boto3_session.client('eks', region_name=region)
    response = client.describe_cluster(name=cluster_name)
    return response['cluster']


@timeit
def load_eks_clusters(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    query: str = """
    MERGE (cluster:EKSCluster{id: {ClusterArn}})
    ON CREATE SET cluster.firstseen = timestamp(),
                cluster.arn = {ClusterArn},
                cluster.name = {ClusterName},
                cluster.region = {Region},
                cluster.created_at = {CreatedAt},
                cluster.borneo_id = apoc.create.uuid()
    SET cluster.lastupdated = {aws_update_tag},
        cluster.endpoint = {ClusterEndpoint},
        cluster.endpoint_public_access = {ClusterEndointPublic},
        cluster.rolearn = {ClusterRoleArn},
        cluster.version = {ClusterVersion},
        cluster.platform_version = {ClusterPlatformVersion},
        cluster.status = {ClusterStatus},
        cluster.audit_logging = {ClusterLogging},
        cluster.secrets_encrypted = {ClusterSecretsEncrypted}
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
            ClusterEndpoint=cluster.get('endpoint'),
            ClusterEndointPublic=cluster.get('resourcesVpcConfig', {}).get('endpointPublicAccess'),
            ClusterRoleArn=cluster.get('roleArn'),
            ClusterVersion=cluster.get('version'),
            ClusterPlatformVersion=cluster.get('platformVersion'),
            ClusterStatus=cluster.get('status'),
            CreatedAt=str(cluster.get('createdAt')),
            ClusterLogging=_process_logging(cluster),
            Region=region,
            aws_update_tag=aws_update_tag,
            AWS_ACCOUNT_ID=current_aws_account_id,
            ClusterSecretsEncrypted=True if ('secrets' in cluster.get('encryptionConfig', [{}])[0].get('resources')) else False
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
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.info("Running EKS cluster cleanup")
    GraphJob.from_node_schema(EKSClusterSchema(), common_job_parameters).run(neo4j_session)


def transform(cluster_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    transformed_list = []
    for cluster_name, cluster_dict in cluster_data.items():
        transformed_dict = cluster_dict.copy()
        transformed_dict['ClusterLogging'] = _process_logging(transformed_dict)
        transformed_dict['ClusterEndpointPublic'] = transformed_dict.get('resourcesVpcConfig', {}).get(
            'endpointPublicAccess',
        )
        if 'createdAt' in transformed_dict:
            transformed_dict['created_at'] = str(transformed_dict['createdAt'])
        transformed_list.append(transformed_dict)
    return transformed_list


@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info("Syncing EKS for region '%s' in account '%s'.", region, current_aws_account_id)

        clusters: List[str] = get_eks_clusters(boto3_session, region)
        cluster_data = {}
        for cluster_name in clusters:
            cluster_data[cluster_name] = get_eks_describe_cluster(boto3_session, region, cluster_name)
        transformed_list = transform(cluster_data)

        load_eks_clusters(neo4j_session, transformed_list, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

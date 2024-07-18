import logging
import time
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.eks.clusters import EKSClusterSchema
from cartography.models.aws.eks.nodegroups import EKSClusterNodeGroupSchema
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_eks_clusters(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = boto3_session.client('eks', region_name=region, config=get_botocore_config())
    clusters: List[str] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        clusters.extend(page['clusters'])

    clusters_data = []
    for cluster in clusters:
        cluster_data = {}
        cluster_data['name'] = cluster
        cluster_data['region'] = region
        clusters_data.append(cluster_data)
    return clusters_data


@timeit
def get_eks_describe_cluster(boto3_session: boto3.session.Session, region: str, cluster_name: str) -> Dict:
    client = boto3_session.client('eks', region_name=region, config=get_botocore_config())
    response = client.describe_cluster(name=cluster_name)
    response['cluster']['region'] = region
    response['cluster']['consolelink'] = aws_console_link.get_console_link(arn=response['cluster']['arn'])
    return response['cluster']


@timeit
def load_eks_clusters(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict[str, Any]],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        EKSClusterSchema(),
        cluster_data,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
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
    run_cleanup_job('aws_import_eks_cleanup.json', neo4j_session, common_job_parameters)


def transform(cluster_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    transformed_list = []
    for cluster_name, cluster_dict in cluster_data.items():
        transformed_dict = cluster_dict.copy()
        transformed_dict['ClusterLogging'] = _process_logging(transformed_dict)
        transformed_dict['consolelink'] = aws_console_link.get_console_link(arn=transformed_dict.get('arn'))
        transformed_dict['ClusterEndpointPublic'] = transformed_dict.get('resourcesVpcConfig', {}).get(
            'endpointPublicAccess',
        )
        if 'createdAt' in transformed_dict:
            transformed_dict['created_at'] = str(transformed_dict['createdAt'])
        transformed_list.append(transformed_dict)
    return transformed_list


@timeit
def get_eks_cluster_nodegroups(boto3_session: boto3.session.Session, region: str, cluster_name: str) -> List[str]:
    client = boto3_session.client('eks', region_name=region, config=get_botocore_config())
    nodegroups: List[str] = []
    paginator = client.get_paginator('list_nodegroups')
    for page in paginator.paginate(clusterName=cluster_name):
        nodegroups.extend(page['nodegroups'])

    nodegroups_data = []
    for nodegroup in nodegroups:
        nodegroup_data = {}
        nodegroup_data['name'] = nodegroup
        nodegroup_data['region'] = region
        nodegroup_data.update(get_eks_describe_cluster_nodegroup(boto3_session, region, cluster_name, nodegroup))
        nodegroups_data.append(nodegroup_data)
    return nodegroups_data


@timeit
def get_eks_describe_cluster_nodegroup(boto3_session: boto3.session.Session, region: str, cluster_name: str, nodegroup_name: str) -> Dict:
    client = boto3_session.client('eks', region_name=region, config=get_botocore_config())
    response = client.describe_nodegroup(clusterName=cluster_name, nodegroupName=nodegroup_name)
    return response['nodegroup']


@timeit
def load_eks_cluster_nodegroups(
        neo4j_session: neo4j.Session,
        nodegroups_data: List[Dict[str, Any]],
        cluster_arn: str,
        aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        EKSClusterNodeGroupSchema(),
        nodegroups_data,
        cluster_arn=cluster_arn,
        lastupdated=aws_update_tag,
    )


@timeit
@aws_handle_regions
def get_auto_scaling_groups(boto3_session: boto3.session.Session, region: str, auto_scaling_groups: List[str]) -> List[Dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs: List[Dict] = []
    try:
        for page in paginator.paginate(AutoScalingGroupNames=auto_scaling_groups):
            asgs.extend(page['AutoScalingGroups'])

    except Exception as e:
        logger.warning(f"Failed retrieve autoscaling groups for region - {region}. Error - {e}")

    return asgs


@timeit
def attact_autoscaling_groups_to_nodegroups(neo4j_session: neo4j.Session, nodegroup_arn: str, auto_scalin_groups: List[Dict], update_tag: int) -> None:
    attach_autoscaling = """
    UNWIND $auto_scalin_groups as agroup
    MERGE (g:AutoScalingGroup{arn: agroup.AutoScalingGroupARN})
    ON CREATE SET g.firstseen = timestamp()
    SET g.lastupdated = $update_tag
    WITH g
    MATCH (ngroup:EKSClusterNodeGroup{arn: $GROUPARN})
    MERGE (g)-[r:ASSOCIATED_WITH]->(ngroup)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        attach_autoscaling,
        auto_scalin_groups=auto_scalin_groups,
        GROUPARN=nodegroup_arn,
        update_tag=update_tag,
    )


@timeit
def sync_eks_cluster_nodegroups(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        clusters_data: List[Dict],
        update_tag: int,
) -> None:
    for cluster in clusters_data:
        nodegroups = get_eks_cluster_nodegroups(boto3_session, cluster["region"], cluster["name"])
        load_eks_cluster_nodegroups(neo4j_session, nodegroups, cluster["arn"], update_tag)
        for nodegroup in nodegroups:
            auto_scalin_groups = []
            for auto_scalin_group in nodegroup.get("resources", {}).get("autoScalingGroups", []):
                auto_scalin_groups.append(auto_scalin_group["name"])
            if auto_scalin_groups:
                auto_scalin_groups = get_auto_scaling_groups(boto3_session, cluster['region'], auto_scalin_groups)
                attact_autoscaling_groups_to_nodegroups(neo4j_session, nodegroup["nodegroupArn"], auto_scalin_groups, update_tag)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EKS for account '%s', at %s.", current_aws_account_id, tic)

    clusters = []
    for region in regions:
        logger.info("Syncing EKS for region '%s' in account '%s'.", region, current_aws_account_id)

        clusters.extend(get_eks_clusters(boto3_session, region))

    logger.info(f"Total EKS Clusters: {len(clusters)}")

    cluster_data: List = []
    for cluster in clusters:
        cluster_data.append(get_eks_describe_cluster(boto3_session, cluster['region'], cluster['name']))

    load_eks_clusters(neo4j_session, cluster_data, current_aws_account_id, update_tag)

    sync_eks_cluster_nodegroups(neo4j_session, boto3_session, cluster_data, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EKS: {toc - tic:0.4f} seconds")

import logging
import time
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j
import uuid

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.emr import EMRClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# EMR API is subject to aggressive throttling, so we need to sleep a second between each call.
LIST_SLEEP = 1
DESCRIBE_SLEEP = 1


@timeit
@aws_handle_regions
def get_emr_clusters(boto3_session: boto3.session.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client('emr', region_name=region, config=get_botocore_config())
    clusters: List[Dict[str, Any]] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        cluster = page['Clusters']
        clusters.extend(cluster)
        time.sleep(LIST_SLEEP)
    return clusters


@timeit
def get_emr_describe_cluster(boto3_session: boto3.session.Session, region: str, cluster_id: str) -> Dict[str, Any]:
    client = boto3_session.client('emr', region_name=region, config=get_botocore_config())
    cluster_details: Dict[str, Any] = {}
    try:
        response = client.describe_cluster(ClusterId=cluster_id)
        cluster_details = response['Cluster']
    except botocore.exceptions.ClientError as e:
        code = e.response['Error']['Code']
        msg = e.response['Error']['Message']
        logger.warning(f"Could not run EMR describe_cluster due to boto3 error {code}: {msg}. Skipping.")
    return cluster_details


@timeit
def load_emr_clusters(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    query = """
    UNWIND {Clusters} as emr_cluster
        MERGE (cluster:EMRCluster{id: emr_cluster.Name})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = emr_cluster.ClusterArn,
            cluster.id = emr_cluster.Id,
            cluster.region = {Region},
            cluster.borneo_id = {cluster_borneo_id}
        SET cluster.name = emr_cluster.Name,
            cluster.instance_collection_type = emr_cluster.InstanceCollectionType,
            cluster.log_encryption_kms_key_id = emr_cluster.LogEncryptionKmsKeyId,
            cluster.requested_ami_version = emr_cluster.RequestedAmiVersion,
            cluster.running_ami_version = emr_cluster.RunningAmiVersion,
            cluster.release_label = emr_cluster.ReleaseLabel,
            cluster.auto_terminate = emr_cluster.AutoTerminate,
            cluster.termination_protected = emr_cluster.TerminationProtected,
            cluster.visible_to_all_users = emr_cluster.VisibleToAllUsers,
            cluster.master_public_dns_name = emr_cluster.MasterPublicDnsName,
            cluster.security_configuration = emr_cluster.SecurityConfiguration,
            cluster.autoscaling_role = emr_cluster.AutoScalingRole,
            cluster.scale_down_behavior = emr_cluster.ScaleDownBehavior,
            cluster.custom_ami_id = emr_cluster.CustomAmiId,
            cluster.repo_upgrade_on_boot = emr_cluster.RepoUpgradeOnBoot,
            cluster.outpost_arn = emr_cluster.OutpostArn,
            cluster.log_uri = emr_cluster.LogUri,
            cluster.servicerole = emr_cluster.ServiceRole,
            cluster.lastupdated = {aws_update_tag}
        WITH cluster

        MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (owner)-[r:RESOURCE]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    logger.info("Loading EMR %d clusters for region '%s' into graph.", len(cluster_data), region)
    neo4j_session.run(
        query,
        Clusters=cluster_data,
        Region=region,
        aws_update_tag=aws_update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
        cluster_borneo_id=uuid.uuid4()
    ).consume()


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running EMR cleanup job.")
    cleanup_job = GraphJob.from_node_schema(EMRClusterSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(f"Syncing EMR for region '{region}' in account '{current_aws_account_id}'.")

        clusters = get_emr_clusters(boto3_session, region)

        cluster_data: List[Dict[str, Any]] = []
        for cluster in clusters:
            cluster_id = cluster['Id']
            cluster_details = get_emr_describe_cluster(boto3_session, region, cluster_id)
            if cluster_details:
                cluster_data.append(cluster_details)
            time.sleep(DESCRIBE_SLEEP)

        load_emr_clusters(neo4j_session, cluster_data, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

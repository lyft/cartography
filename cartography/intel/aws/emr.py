import logging
import time
from dataclasses import dataclass
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

# EMR API is subject to aggressive throttling, so we need to sleep a second between each call.
LIST_SLEEP = 1
DESCRIBE_SLEEP = 1


@timeit
@aws_handle_regions
def get_emr_clusters(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('emr', region_name=region, config=get_botocore_config())
    clusters: List[Dict] = []
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        cluster = page['Clusters']
        clusters.extend(cluster)
        time.sleep(LIST_SLEEP)
    return clusters


@timeit
def get_emr_describe_cluster(boto3_session: boto3.session.Session, region: str, cluster_id: str) -> Dict:
    client = boto3_session.client('emr', region_name=region, config=get_botocore_config())
    cluster_details: Dict = {}
    try:
        response = client.describe_cluster(ClusterId=cluster_id)
        cluster_details = response['Cluster']
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not run EMR describe_cluster due to boto3 error %s: %s. Skipping.",
            e.response['Error']['Code'],
            e.response['Error']['Message'],
        )
    return cluster_details


@dataclass(frozen=True)
class EMRClusterNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('ClusterArn')
    auto_terminate: PropertyRef = PropertyRef('AutoTerminate')
    autoscaling_role: PropertyRef = PropertyRef('AutoScalingRole')
    custom_ami_id: PropertyRef = PropertyRef('CustomAmiId')
    firstseen: PropertyRef = PropertyRef('firstseen')
    id: PropertyRef = PropertyRef('Id')
    instance_collection_type: PropertyRef = PropertyRef('InstanceCollectionType')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    log_encryption_kms_key_id: PropertyRef = PropertyRef('LogEncryptionKmsKeyId')
    log_uri: PropertyRef = PropertyRef('LogUri')
    master_public_dns_name: PropertyRef = PropertyRef('MasterPublicDnsName')
    name: PropertyRef = PropertyRef('Name')
    outpost_arn: PropertyRef = PropertyRef('OutpostArn')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    release_label: PropertyRef = PropertyRef('ReleaseLabel')
    repo_upgrade_on_boot: PropertyRef = PropertyRef('RepoUpgradeOnBoot')
    requested_ami_version: PropertyRef = PropertyRef('RequestedAmiVersion')
    running_ami_version: PropertyRef = PropertyRef('RunningAmiVersion')
    scale_down_behavior: PropertyRef = PropertyRef('ScaleDownBehavior')
    security_configuration: PropertyRef = PropertyRef('SecurityConfiguration')
    servicerole: PropertyRef = PropertyRef('ServiceRole')
    termination_protected: PropertyRef = PropertyRef('TerminationProtected')
    visible_to_all_users: PropertyRef = PropertyRef('VisibleToAllUsers')


@dataclass(frozen=True)
class EMRClusterToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:EMRCluster)<-[:RESOURCE]-(:AWSAccount)
class EMRClusterToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AccountId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EMRClusterToAwsAccountRelProperties = EMRClusterToAwsAccountRelProperties()


@dataclass(frozen=True)
class EMRClusterSchema(CartographyNodeSchema):
    label: str = 'EMRCluster'
    properties: EMRClusterNodeProperties = EMRClusterNodeProperties()
    sub_resource_relationship: EMRClusterToAWSAccount = EMRClusterToAWSAccount()


@timeit
def load_emr_clusters(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict],
        region: str,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    logger.info("Loading EMR %d clusters for region '%s' into graph.", len(cluster_data), region)

    ingestion_query = build_ingestion_query(EMRClusterSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        cluster_data,
        lastupdated=aws_update_tag,
        Region=region,
        AccountId=current_aws_account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running EMR cleanup job.")
    run_cleanup_job('aws_import_emr_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EMR for region '%s' in account '%s'.", region, current_aws_account_id)

        clusters = get_emr_clusters(boto3_session, region)

        cluster_data: List[Dict] = []
        for cluster in clusters:
            cluster_id = cluster['Id']
            cluster_details = get_emr_describe_cluster(boto3_session, region, cluster_id)
            if cluster_details:
                cluster_data.append(cluster_details)
            time.sleep(DESCRIBE_SLEEP)

        load_emr_clusters(neo4j_session, cluster_data, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

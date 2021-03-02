import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_auto_scaling_groups(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs: List[Dict] = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return asgs


@timeit
def load_ec2_auto_scaling_groups(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_group = """
    MERGE (group:AutoScalingGroup{arn: {ARN}})
    ON CREATE SET group.firstseen = timestamp(), group.name = {Name}, group.createdtime = {CreatedTime}
    SET group.lastupdated = {update_tag}, group.launchconfigurationname = {LaunchConfigurationName},
    group.maxsize = {MaxSize}, group.region={Region}
    WITH group
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    ingest_vpc = """
    MERGE (subnet:EC2Subnet{subnetid: {SubnetId}})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.lastupdated = {update_tag}
    WITH subnet
    MATCH (group:AutoScalingGroup{arn: {GROUPARN}})
    MERGE (subnet)<-[r:VPC_IDENTIFIER]-(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    ingest_instance = """
    MERGE (instance:Instance:EC2Instance{id: {InstanceId}})
    ON CREATE SET instance.firstseen = timestamp()
    SET instance.instanceid = {InstanceId}, instance.lastupdated = {update_tag}, instance.region={Region}
    WITH instance
    MATCH (group:AutoScalingGroup{arn: {GROUPARN}})
    MERGE (instance)-[r:MEMBER_AUTO_SCALE_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    WITH instance
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    for group in data:
        name = group["AutoScalingGroupName"]
        createtime = group.get("CreatedTime")
        lauchconfig_name = group.get("LaunchConfigurationName")
        group_arn = group["AutoScalingGroupARN"]
        max_size = group["MaxSize"]

        neo4j_session.run(
            ingest_group,
            ARN=group_arn,
            Name=name,
            CreatedTime=str(createtime),
            LaunchConfigurationName=lauchconfig_name,
            MaxSize=max_size,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            update_tag=update_tag,
        )

        if group.get('VPCZoneIdentifier'):
            vpclist = group["VPCZoneIdentifier"]
            for vpc in str(vpclist).split(','):
                neo4j_session.run(
                    ingest_vpc,
                    SubnetId=vpc,
                    GROUPARN=group_arn,
                    update_tag=update_tag,
                )

        if group.get("Instances"):
            for instance in group["Instances"]:
                instanceid = instance["InstanceId"]
                neo4j_session.run(
                    ingest_instance,
                    InstanceId=instanceid,
                    GROUPARN=group_arn,
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    Region=region,
                    update_tag=update_tag,
                )


@timeit
def cleanup_ec2_auto_scaling_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_auto_scaling_groups(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_auto_scaling_groups(boto3_session, region)
        load_ec2_auto_scaling_groups(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters)

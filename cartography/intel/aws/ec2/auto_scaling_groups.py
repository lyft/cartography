import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_auto_scaling_groups(boto3_session, region):
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return asgs


@timeit
def load_ec2_auto_scaling_groups(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_group = """
    MERGE (group:AutoScalingGroup{arn: {ARN}})
    ON CREATE SET group.firstseen = timestamp(), group.name = {Name}, group.createdtime = {CreatedTime}
    SET group.lastupdated = {aws_update_tag}, group.launchconfigurationname = {LaunchConfigurationName},
    group.maxsize = {MaxSize}, group.region={Region}
    WITH group
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_vpc = """
    MERGE (subnet:EC2Subnet{subnetid: {SubnetId}})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.lastupdated = {aws_update_tag}
    WITH subnet
    MATCH (group:AutoScalingGroup{arn: {GROUPARN}})
    MERGE (subnet)<-[r:VPC_IDENTIFIER]-(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_instance = """
    MERGE (instance:Instance:EC2Instance{id: {InstanceId}})
    ON CREATE SET instance.firstseen = timestamp()
    SET instance.instanceid = {InstanceId}, instance.lastupdated = {aws_update_tag}, instance.region={Region}
    WITH instance
    MATCH (group:AutoScalingGroup{arn: {GROUPARN}})
    MERGE (instance)-[r:MEMBER_AUTO_SCALE_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH instance
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
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
            aws_update_tag=aws_update_tag,
        )

        if group.get('VPCZoneIdentifier'):
            vpclist = group["VPCZoneIdentifier"]
            for vpc in str(vpclist).split(','):
                neo4j_session.run(
                    ingest_vpc,
                    SubnetId=vpc,
                    GROUPARN=group_arn,
                    aws_update_tag=aws_update_tag,
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
                    aws_update_tag=aws_update_tag,
                )


@timeit
def cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters):
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_auto_scaling_groups(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_auto_scaling_groups(boto3_session, region)
        load_ec2_auto_scaling_groups(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters)

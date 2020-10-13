import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_load_balancer_v2_listeners(client, load_balancer_arn):
    paginator = client.get_paginator('describe_listeners')
    listeners = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        listeners.extend(page['Listeners'])

    return listeners


@timeit
def get_load_balancer_v2_target_groups(client, load_balancer_arn):
    paginator = client.get_paginator('describe_target_groups')
    target_groups = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        target_groups.extend(page['TargetGroups'])

    # Add instance data
    for target_group in target_groups:
        target_group['Targets'] = []
        target_health = client.describe_target_health(TargetGroupArn=target_group['TargetGroupArn'])
        for target_health_description in target_health['TargetHealthDescriptions']:
            target_group['Targets'].append(target_health_description['Target']['Id'])

    return target_groups


@timeit
@aws_handle_regions
def get_loadbalancer_v2_data(boto3_session, region):
    client = boto3_session.client('elbv2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_load_balancers')
    elbv2s = []
    for page in paginator.paginate():
        elbv2s.extend(page['LoadBalancers'])

    # Make extra calls to get listeners
    for elbv2 in elbv2s:
        elbv2['Listeners'] = get_load_balancer_v2_listeners(client, elbv2['LoadBalancerArn'])
        elbv2['TargetGroups'] = get_load_balancer_v2_target_groups(client, elbv2['LoadBalancerArn'])
    return elbv2s


@timeit
def load_load_balancer_v2s(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_load_balancer_v2 = """
    MERGE (elbv2:LoadBalancerV2{id: {ID}})
    ON CREATE SET elbv2.firstseen = timestamp(), elbv2.createdtime = {CREATED_TIME}
    SET elbv2.lastupdated = {aws_update_tag}, elbv2.name = {NAME}, elbv2.dnsname = {DNS_NAME},
    elbv2.canonicalhostedzonenameid = {HOSTED_ZONE_NAME_ID},
    elbv2.type = {ELBv2_TYPE},
    elbv2.scheme = {SCHEME}, elbv2.region = {Region}
    WITH elbv2
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(elbv2)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for lb in data:
        load_balancer_id = lb["DNSName"]

        neo4j_session.run(
            ingest_load_balancer_v2,
            ID=load_balancer_id,
            CREATED_TIME=str(lb["CreatedTime"]),
            NAME=lb["LoadBalancerName"],
            DNS_NAME=load_balancer_id,
            HOSTED_ZONE_NAME_ID=lb.get("CanonicalHostedZoneNameID"),
            ELBv2_TYPE=lb.get("Type"),
            SCHEME=lb.get("Scheme"),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag,
        )

        if lb["AvailabilityZones"]:
            az = lb["AvailabilityZones"]
            load_load_balancer_v2_subnets(neo4j_session, load_balancer_id, az, region, aws_update_tag)

        # NLB's don't have SecurityGroups, so check for one first.
        if 'SecurityGroups' in lb and lb["SecurityGroups"]:
            ingest_load_balancer_v2_security_group = """
            MATCH (elbv2:LoadBalancerV2{id: {ID}}),
            (group:EC2SecurityGroup{groupid: {GROUP_ID}})
            MERGE (elbv2)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {aws_update_tag}
            """
            for group in lb["SecurityGroups"]:
                neo4j_session.run(
                    ingest_load_balancer_v2_security_group,
                    ID=load_balancer_id,
                    GROUP_ID=str(group),
                    aws_update_tag=aws_update_tag,
                )

        if lb['Listeners']:
            load_load_balancer_v2_listeners(neo4j_session, load_balancer_id, lb['Listeners'], aws_update_tag)

        if lb['TargetGroups']:
            load_load_balancer_v2_target_groups(
                neo4j_session, load_balancer_id, lb['TargetGroups'],
                current_aws_account_id, aws_update_tag,
            )

        if lb['TargetGroups']:
            load_load_balancer_v2_target_groups(
                neo4j_session, load_balancer_id, lb['TargetGroups'],
                current_aws_account_id, aws_update_tag,
            )


@timeit
def load_load_balancer_v2_subnets(neo4j_session, load_balancer_id, az_data, region, aws_update_tag):
    ingest_load_balancer_subnet = """
    MATCH (elbv2:LoadBalancerV2{id: {ID}})
    MERGE (subnet:EC2Subnet{subnetid: {SubnetId}})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.region = {region}, subnet.lastupdated = {aws_update_tag}
    WITH elbv2, subnet
    MERGE (elbv2)-[r:SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for az in az_data:
        neo4j_session.run(
            ingest_load_balancer_subnet,
            ID=load_balancer_id,
            SubnetId=az['SubnetId'],
            region=region,
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_load_balancer_v2_target_groups(
    neo4j_session, load_balancer_id, target_groups, current_aws_account_id,
    aws_update_tag,
):
    ingest_instances = """
    MATCH (elbv2:LoadBalancerV2{id: {ID}}), (instance:EC2Instance{instanceid: {INSTANCE_ID}})
    MERGE (elbv2)-[r:EXPOSE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH instance
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for target_group in target_groups:

        if not target_group['TargetType'] == 'instance':
            # Only working on EC2 Instances now. TODO: Add IP & Lambda EXPOSE.
            continue

        for instance in target_group["Targets"]:
            neo4j_session.run(
                ingest_instances,
                ID=load_balancer_id,
                INSTANCE_ID=instance,
                AWS_ACCOUNT_ID=current_aws_account_id,
                aws_update_tag=aws_update_tag,
            )


@timeit
def load_load_balancer_v2_listeners(neo4j_session, load_balancer_id, listener_data, aws_update_tag):
    ingest_listener = """
    MATCH (elbv2:LoadBalancerV2{id: {LoadBalancerId}})
    WITH elbv2
    UNWIND {Listeners} as data
        MERGE (l:Endpoint:ELBV2Listener{id: data.ListenerArn})
        ON CREATE SET l.port = data.Port, l.protocol = data.Protocol,
        l.firstseen = timestamp(),
        l.targetgrouparn = data.TargetGroupArn
        SET l.lastupdated = {aws_update_tag}
        WITH l, elbv2
        MERGE (elbv2)-[r:ELBV2_LISTENER]->(l)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_listener,
        LoadBalancerId=load_balancer_id,
        Listeners=listener_data,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_load_balancer_v2s(neo4j_session, common_job_parameters):
    """Delete elbv2's and dependent resources in the DB without the most recent lastupdated tag."""
    run_cleanup_job('aws_ingest_load_balancers_v2_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_load_balancer_v2s(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 load balancers v2 for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_loadbalancer_v2_data(boto3_session, region)
        load_load_balancer_v2s(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_load_balancer_v2s(neo4j_session, common_job_parameters)

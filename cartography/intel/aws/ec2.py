import botocore.config
import logging
import time

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# TODO memoize this
def _get_botocore_config():
    return botocore.config.Config(
        read_timeout=360,
        retries={
            'max_attempts': 10,
        }
    )


def get_ec2_regions(session):
    client = session.client('ec2')
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]


def get_ec2_security_group_data(session, region):
    client = session.client('ec2', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_security_groups')
    security_groups = []
    for page in paginator.paginate():
        security_groups.extend(page['SecurityGroups'])
    return {'SecurityGroups': security_groups}


def get_ec2_instances(session, region):
    client = session.client('ec2', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_instances')
    reservations = []
    for page in paginator.paginate():
        reservations.extend(page['Reservations'])
    return {'Reservations': reservations}


def get_ec2_auto_scaling_groups(session, region):
    client = session.client('autoscaling', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return {'AutoScalingGroups': asgs}


def get_loadbalancer_data(session, region):
    client = session.client('elb', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_load_balancers')
    elbs = []
    for page in paginator.paginate():
        elbs.extend(page['LoadBalancerDescriptions'])
    return {'LoadBalancerDescriptions': elbs}


def load_ec2_instances(session, data, region, current_aws_account_id, aws_update_tag):
    ingest_reservation = """
    MERGE (reservation:EC2Reservation{reservationid: {ReservationId}})
    ON CREATE SET reservation.firstseen = timestamp()
    SET reservation.ownerid = {OwnerId}, reservation.requesterid = {RequesterId}, reservation.region = {Region},
    reservation.lastupdated = {aws_update_tag}
    WITH reservation
    MATCH (awsAccount:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (awsAccount)-[r:RESOURCE]->(reservation)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_instance = """
    MERGE (instance:EC2Instance{instanceid: {InstanceId}})
    ON CREATE SET instance.firstseen = timestamp()
    SET instance.publicdnsname = {PublicDnsName}, instance.privateipaddress = {PrivateIpAddress},
    instance.imageid = {ImageId}, instance.instancetype = {InstanceType}, instance.monitoringstate = {MonitoringState},
    instance.state = {State}, instance.launchtime = {LaunchTime}, instance.launchtimeunix = {LaunchTimeUnix},
    instance.region = {Region}, instance.lastupdated = {aws_update_tag}
    WITH instance
    MERGE (subnet:EC2Subnet{subnetid: {SubnetId}})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.region = {Region}, subnet.lastupdated = {aws_update_tag}
    MERGE (instance)-[r:PART_OF_SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH instance
    MATCH (rez:EC2Reservation{reservationid: {ReservationId}})
    MERGE (instance)-[r:MEMBER_OF_EC2_RESERVATION]->(rez)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH instance
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_security_groups = """
    MERGE (group:EC2SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.name = {GroupName}, group.region = {Region}, group.lastupdated = {aws_update_tag}
    WITH group
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH group
    MATCH (instance:EC2Instance{instanceid: {InstanceId}})
    MERGE (instance)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for reservation in data['Reservations']:
        reservation_id = reservation["ReservationId"]

        session.run(
            ingest_reservation,
            ReservationId=reservation_id,
            OwnerId=reservation.get("OwnerId", ""),
            RequesterId=reservation.get("RequesterId", ""),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag
        )

        for instance in reservation["Instances"]:
            instanceid = instance["InstanceId"]

            monitoring_state = instance.get("Monitoring", {}).get("State", "")

            instance_state = instance.get("State", {}).get("Name", "")

            # NOTE this is a hack because we're using a version of Neo4j that doesn't support temporal data types
            launch_time = instance.get("LaunchTime", "")
            if launch_time:
                launch_time_unix = time.mktime(launch_time.timetuple())
            else:
                launch_time_unix = ""

            session.run(
                ingest_instance,
                InstanceId=instanceid,
                PublicDnsName=instance.get("PublicDnsName", ""),
                PublicIpAddress=instance.get("PublicIpAddress", ""),
                PrivateIpAddress=instance.get("PrivateIpAddress", ""),
                ImageId=instance.get("ImageId", ""),
                SubnetId=instance.get("SubnetId", ""),
                InstanceType=instance.get("InstanceType", ""),
                ReservationId=reservation_id,
                MonitoringState=monitoring_state,
                LaunchTime=str(launch_time),
                LaunchTimeUnix=launch_time_unix,
                State=instance_state,
                AWS_ACCOUNT_ID=current_aws_account_id,
                Region=region,
                aws_update_tag=aws_update_tag
            )

            if instance.get("SecurityGroups"):
                for group in instance["SecurityGroups"]:
                    session.run(
                        ingest_security_groups,
                        GroupId=group["GroupId"],
                        GroupName=group.get("GroupName", ""),
                        InstanceId=instanceid,
                        Region=region,
                        AWS_ACCOUNT_ID=current_aws_account_id,
                        aws_update_tag=aws_update_tag
                    )

            load_ec2_instance_network_interfaces(session, instance, aws_update_tag)


def load_ec2_instance_network_interfaces(session, instance_data, aws_update_tag):
    ingest_network_interface = """
    MATCH (instance:EC2Instance{instanceid: {InstanceId}})
    MERGE (interface:NetworkInterface{id: {NetworkId}})
    ON CREATE SET interface.firstseen = timestamp()
    SET interface.status = {Status}, interface.mac_address = {MacAddress}, interface.description = {Description},
    interface.private_dns_name = {PrivateDnsName}, interface.private_ip_address = {PrivateIpAddress},
    interface.lastupdated = {aws_update_tag}
    MERGE (instance)-[r:NETWORK_INTERFACE]->(interface)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH interface
    MERGE (subnet:EC2Subnet{subnetid: {SubnetId}})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.lastupdated = {aws_update_tag}
    MERGE (interface)-[r:PART_OF_SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_network_group = """
    MATCH (interface:NetworkInterface{id: {NetworkId}}),
    (group:EC2SecurityGroup{groupid: {GroupId}})
    MERGE (interface)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    instance_id = instance_data["InstanceId"]

    for interface in instance_data["NetworkInterfaces"]:
        session.run(
            ingest_network_interface,
            InstanceId=instance_id,
            NetworkId=interface["NetworkInterfaceId"],
            Status=interface["Status"],
            MacAddress=interface.get("MacAddress", ""),
            Description=interface.get("Description", ""),
            PrivateDnsName=interface.get("PrivateDnsName", ""),
            PrivateIpAddress=interface.get("PrivateIpAddress", ""),
            SubnetId=interface.get("SubnetId", ""),
            aws_update_tag=aws_update_tag
        )

        for group in interface.get("Groups", []):
            session.run(
                ingest_network_group,
                NetworkId=interface["NetworkInterfaceId"],
                GroupId=group["GroupId"],
                aws_update_tag=aws_update_tag
            )


def load_ec2_security_groupinfo(session, data, region, current_aws_account_id, aws_update_tag):
    ingest_security_group = """
    MERGE (group:EC2SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.name = {GroupName}, group.description = {Description}, group.region = {Region},
    group.lastupdated = {aws_update_tag}
    WITH group
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for group in data["SecurityGroups"]:
        group_id = group["GroupId"]

        session.run(
            ingest_security_group,
            GroupId=group_id,
            GroupName=group.get("GroupName", ""),
            Description=group.get("Description", ""),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag
        )

        load_ec2_security_group_rule(session, group, "IpPermissions", aws_update_tag)
        load_ec2_security_group_rule(session, group, "IpPermissionEgress", aws_update_tag)


def load_ec2_security_group_rule(session, group, rule_type, aws_update_tag):
    ingest_rule = """
    MERGE (rule:#RULE_TYPE#{ruleid: {RuleId}})
    ON CREATE SET rule :IpRule, rule.firstseen = timestamp(), rule.fromport = {FromPort}, rule.toport = {ToPort},
    rule.protocol = {Protocol}
    SET rule.lastupdated = {aws_update_tag}
    WITH rule
    MATCH (group:EC2SecurityGroup{groupid: {GroupId}})
    MERGE (group)<-[r:MEMBER_OF_EC2_SECURITY_GROUP]-(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag};
    """

    ingest_rule_group_pair = """
    MERGE (group:EC2SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.lastupdated = {aws_update_tag}
    WITH group
    MATCH (inbound:IpRule{ruleid: {RuleId}})
    MERGE (inbound)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_range = """
    MERGE (range:IpRange{id: {RangeId}})
    ON CREATE SET range.firstseen = timestamp(), range.range = {RangeId}
    SET range.lastupdated = {aws_update_tag}
    WITH range
    MATCH (rule:IpRule{ruleid: {RuleId}})
    MERGE (rule)<-[r:MEMBER_OF_IP_RULE]-(range)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    group_id = group["GroupId"]
    rule_type_map = {"IpPermissions": "IpPermissionInbound", "IpPermissionEgress": "IpPermissionEgress"}

    if group.get(rule_type):
        for rule in group[rule_type]:
            protocol = rule.get("IpProtocol", "all")
            from_port = rule.get("FromPort", "")
            to_port = rule.get("ToPort", "")

            ruleid = "{0}/{1}/{2}{3}{4}".format(group_id, rule_type, from_port, to_port, protocol)
            # NOTE Cypher query syntax is incompatible with Python string formatting, so we have to do this awkward
            # NOTE manual formatting instead.
            session.run(
                ingest_rule.replace("#RULE_TYPE#", rule_type_map[rule_type]),
                RuleId=ruleid,
                FromPort=from_port,
                ToPort=to_port,
                Protocol=protocol,
                GroupId=group_id,
                aws_update_tag=aws_update_tag
            )

            session.run(
                ingest_rule_group_pair,
                GroupId=group_id,
                RuleId=ruleid,
                aws_update_tag=aws_update_tag
            )

            for ip_range in rule["IpRanges"]:
                range_id = ip_range["CidrIp"]
                session.run(
                    ingest_range,
                    RangeId=range_id,
                    RuleId=ruleid,
                    aws_update_tag=aws_update_tag
                )


def load_ec2_auto_scaling_groups(session, data, region, current_aws_account_id, aws_update_tag):
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
    MERGE (instance:EC2Instance{instanceid: {InstanceId}})
    ON CREATE SET instance.firstseen = timestamp()
    SET instance.lastupdated = {aws_update_tag}, instance.region={Region}
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

    for group in data["AutoScalingGroups"]:
        name = group["AutoScalingGroupName"]
        createtime = group.get("CreatedTime", "")
        lauchconfig_name = group.get("LaunchConfigurationName", "")
        group_arn = group["AutoScalingGroupARN"]
        max_size = group["MaxSize"]

        session.run(
            ingest_group,
            ARN=group_arn,
            Name=name,
            CreatedTime=str(createtime),
            LaunchConfigurationName=lauchconfig_name,
            MaxSize=max_size,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag
        )

        if group.get('VPCZoneIdentifier'):
            vpclist = group["VPCZoneIdentifier"]
            for vpc in str(vpclist).split(','):
                session.run(
                    ingest_vpc,
                    SubnetId=vpc,
                    GROUPARN=group_arn,
                    aws_update_tag=aws_update_tag
                )

        if group.get("Instances"):
            for instance in group["Instances"]:
                instanceid = instance["InstanceId"]
                session.run(
                    ingest_instance,
                    InstanceId=instanceid,
                    GROUPARN=group_arn,
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    Region=region,
                    aws_update_tag=aws_update_tag
                )


def load_load_balancers(session, data, region, current_aws_account_id, aws_update_tag):
    ingest_load_balancer = """
    MERGE (elb:LoadBalancer{id: {ID}})
    ON CREATE SET elb.firstseen = timestamp(), elb.createdtime = {CREATED_TIME}
    SET elb.lastupdated = {aws_update_tag}, elb.name = {NAME}, elb.dnsname = {DNS_NAME},
    elb.canonicalhostedzonename = {HOSTED_ZONE_NAME}, elb.canonicalhostedzonenameid = {HOSTED_ZONE_NAME_ID},
    elb.scheme = {SCHEME}, elb.region = {Region}
    WITH elb
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(elb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_load_balancersource_security_group = """
    MATCH (elb:LoadBalancer{id: {ID}}),
    (group:EC2SecurityGroup{name: {GROUP_NAME}})
    MERGE (elb)-[r:SOURCE_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_load_balancer_security_group = """
    MATCH (elb:LoadBalancer{id: {ID}}),
    (group:EC2SecurityGroup{groupid: {GROUP_ID}})
    MERGE (elb)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_instances = """
    MATCH (elb:LoadBalancer{id: {ID}}), (instance:EC2Instance{instanceid: {INSTANCE_ID}})
    MERGE (elb)-[r:EXPOSE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH instance
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for lb in data['LoadBalancerDescriptions']:
        load_balancer_id = lb["DNSName"]

        session.run(
            ingest_load_balancer,
            ID=load_balancer_id,
            CREATED_TIME=str(lb["CreatedTime"]),
            NAME=lb["LoadBalancerName"],
            DNS_NAME=load_balancer_id,
            HOSTED_ZONE_NAME=lb.get("CanonicalHostedZoneName", ""),
            HOSTED_ZONE_NAME_ID=lb.get("CanonicalHostedZoneNameID", ""),
            SCHEME=lb.get("Scheme", ""),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag
        )

        if lb["Subnets"]:
            load_load_balancer_subnets(session, load_balancer_id, lb["Subnets"], aws_update_tag)

        if lb["SecurityGroups"]:
            for group in lb["SecurityGroups"]:
                session.run(
                    ingest_load_balancer_security_group,
                    ID=load_balancer_id,
                    GROUP_ID=str(group),
                    aws_update_tag=aws_update_tag
                )

        if lb["SourceSecurityGroup"]:
            source_group = lb["SourceSecurityGroup"]
            session.run(
                ingest_load_balancersource_security_group,
                ID=load_balancer_id,
                GROUP_NAME=source_group["GroupName"],
                aws_update_tag=aws_update_tag
            )

        if lb["Instances"]:
            for instance in lb["Instances"]:
                session.run(
                    ingest_instances,
                    ID=load_balancer_id,
                    INSTANCE_ID=instance["InstanceId"],
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    aws_update_tag=aws_update_tag
                )

        if lb["ListenerDescriptions"]:
            load_load_balancer_listeners(session, load_balancer_id, lb["ListenerDescriptions"], aws_update_tag)


def load_load_balancer_subnets(session, load_balancer_id, subnets_data, aws_update_tag):
    ingest_load_balancer_subnet = """
    MATCH (elb:LoadBalancer{id: {ID}}), (subnet:EC2Subnet{subnetid: {SUBNET_ID}})
    MERGE (elb)-[r:SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for subnet_id in subnets_data:
        session.run(
            ingest_load_balancer_subnet,
            ID=load_balancer_id,
            SUBNET_ID=subnet_id,
            aws_update_tag=aws_update_tag
        )


def load_load_balancer_listeners(session, load_balancer_id, listener_data, aws_update_tag):
    ingest_listener = """
    MATCH (elb:LoadBalancer{id: {LoadBalancerId}})
    WITH elb
    UNWIND {Listeners} as data
        MERGE (l:Endpoint:ELBListener{id: elb.id + toString(data.Listener.LoadBalancerPort) +
                toString(data.Listener.Protocol)})
        ON CREATE SET l.port = data.Listener.LoadBalancerPort, l.protocol = data.Listener.Protocol,
        l.firstseen = timestamp()
        SET l.instance_port = data.Listener.InstancePort, l.instance_protocol = data.Listener.InstanceProtocol,
        l.lastupdated = {aws_update_tag}
        WITH l, elb
        MERGE (elb)-[r:ELB_LISTENER]->(l)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    session.run(
        ingest_listener,
        LoadBalancerId=load_balancer_id,
        Listeners=listener_data,
        aws_update_tag=aws_update_tag
    )


def cleanup_ec2_security_groupinfo(session, common_job_parameters):
    run_cleanup_job(
        'aws_import_ec2_security_groupinfo_cleanup.json',
        session,
        common_job_parameters
    )


def cleanup_ec2_instances(session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', session, common_job_parameters)


def cleanup_ec2_auto_scaling_groups(session, common_job_parameters):
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        session,
        common_job_parameters
    )


def cleanup_load_balancers(session, common_job_parameters):
    run_cleanup_job('aws_ingest_load_balancers_cleanup.json', session, common_job_parameters)


def sync_ec2_security_groupinfo(session, boto3_session, regions, current_aws_account_id, aws_update_tag,
                                common_job_parameters):
    for region in regions:
        logger.debug("Syncing EC2 security groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_security_group_data(boto3_session, region)
        load_ec2_security_groupinfo(session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_security_groupinfo(session, common_job_parameters)


def sync_ec2_instances(session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.debug("Syncing EC2 instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_instances(boto3_session, region)
        load_ec2_instances(session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_instances(session, common_job_parameters)


def sync_ec2_auto_scaling_groups(session, boto3_session, regions, current_aws_account_id, aws_update_tag,
                                 common_job_parameters):
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_auto_scaling_groups(boto3_session, region)
        load_ec2_auto_scaling_groups(session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_auto_scaling_groups(session, common_job_parameters)


def sync_load_balancers(session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.debug("Syncing EC2 load balancers for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_loadbalancer_data(boto3_session, region)
        load_load_balancers(session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_load_balancers(session, common_job_parameters)

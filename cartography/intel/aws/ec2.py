import logging
import time

import botocore.config

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# TODO memoize this
def _get_botocore_config():
    return botocore.config.Config(
        read_timeout=360,
        retries={
            'max_attempts': 10,
        },
    )


def get_ec2_regions(boto3_session):
    client = boto3_session.client('ec2')
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]


def get_ec2_security_group_data(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_security_groups')
    security_groups = []
    for page in paginator.paginate():
        security_groups.extend(page['SecurityGroups'])
    return {'SecurityGroups': security_groups}


def get_ec2_key_pairs(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=_get_botocore_config())
    result = client.describe_key_pairs()
    return result


def get_ec2_instances(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_instances')
    reservations = []
    for page in paginator.paginate():
        reservations.extend(page['Reservations'])
    return {'Reservations': reservations}


def get_ec2_auto_scaling_groups(boto3_session, region):
    client = boto3_session.client('autoscaling', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return {'AutoScalingGroups': asgs}


def get_loadbalancer_data(boto3_session, region):
    client = boto3_session.client('elb', region_name=region, config=_get_botocore_config())
    paginator = client.get_paginator('describe_load_balancers')
    elbs = []
    for page in paginator.paginate():
        elbs.extend(page['LoadBalancerDescriptions'])
    return {'LoadBalancerDescriptions': elbs}


def get_ec2_vpc_peering(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=_get_botocore_config())
    # paginator not supported by boto
    return client.describe_vpc_peering_connections()


def get_ec2_vpcs(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=_get_botocore_config())
    # paginator not supported by boto
    return client.describe_vpcs()


def load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: {ARN}, id: {ARN}})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = {KeyName}, keypair.keyfingerprint = {KeyFingerprint}, keypair.region = {Region},
    keypair.lastupdated = {aws_update_tag}
    WITH keypair
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for key_pair in data['KeyPairs']:
        key_name = key_pair["KeyName"]
        key_fingerprint = key_pair.get("KeyFingerprint")
        key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'

        neo4j_session.run(
            ingest_key_pair,
            ARN=key_pair_arn,
            KeyName=key_name,
            KeyFingerprint=key_fingerprint,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag,
        )


def load_ec2_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
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
    MERGE (instance:Instance:EC2Instance{instanceid: {InstanceId}})
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

    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: {KeyPairARN}, id: {KeyPairARN}})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = {KeyName}, keypair.region = {Region}, keypair.lastupdated = {aws_update_tag}
    WITH keypair
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    with keypair
    MATCH (instance:EC2Instance{instanceid: {InstanceId}})
    MERGE (instance)<-[r:SSH_LOGIN_TO]-(keypair)
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

        neo4j_session.run(
            ingest_reservation,
            ReservationId=reservation_id,
            OwnerId=reservation.get("OwnerId", ""),
            RequesterId=reservation.get("RequesterId", ""),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag,
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

            neo4j_session.run(
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
                aws_update_tag=aws_update_tag,
            )

            if instance.get("KeyName"):
                key_name = instance["KeyName"]
                key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'
                neo4j_session.run(
                    ingest_key_pair,
                    KeyPairARN=key_pair_arn,
                    KeyName=key_name,
                    Region=region,
                    InstanceId=instanceid,
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    aws_update_tag=aws_update_tag,
                )

            if instance.get("SecurityGroups"):
                for group in instance["SecurityGroups"]:
                    neo4j_session.run(
                        ingest_security_groups,
                        GroupId=group["GroupId"],
                        GroupName=group.get("GroupName", ""),
                        InstanceId=instanceid,
                        Region=region,
                        AWS_ACCOUNT_ID=current_aws_account_id,
                        aws_update_tag=aws_update_tag,
                    )

            load_ec2_instance_network_interfaces(neo4j_session, instance, aws_update_tag)


def load_ec2_instance_network_interfaces(neo4j_session, instance_data, aws_update_tag):
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
        neo4j_session.run(
            ingest_network_interface,
            InstanceId=instance_id,
            NetworkId=interface["NetworkInterfaceId"],
            Status=interface["Status"],
            MacAddress=interface.get("MacAddress", ""),
            Description=interface.get("Description", ""),
            PrivateDnsName=interface.get("PrivateDnsName", ""),
            PrivateIpAddress=interface.get("PrivateIpAddress", ""),
            SubnetId=interface.get("SubnetId", ""),
            aws_update_tag=aws_update_tag,
        )

        for group in interface.get("Groups", []):
            neo4j_session.run(
                ingest_network_group,
                NetworkId=interface["NetworkInterfaceId"],
                GroupId=group["GroupId"],
                aws_update_tag=aws_update_tag,
            )


def load_ec2_security_groupinfo(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
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
    WITH group
    MATCH (vpc:AWSVpc{id: {VpcId}})
    MERGE (vpc)-[rg:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET rg.firstseen = timestamp()
    """

    for group in data["SecurityGroups"]:
        group_id = group["GroupId"]

        neo4j_session.run(
            ingest_security_group,
            GroupId=group_id,
            GroupName=group.get("GroupName", ""),
            Description=group.get("Description", ""),
            VpcId=group.get("VpcId", None),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        load_ec2_security_group_rule(neo4j_session, group, "IpPermissions", aws_update_tag)
        load_ec2_security_group_rule(neo4j_session, group, "IpPermissionEgress", aws_update_tag)


def load_ec2_security_group_rule(neo4j_session, group, rule_type, aws_update_tag):
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

            ruleid = f"{group_id}/{rule_type}/{from_port}{to_port}{protocol}"
            # NOTE Cypher query syntax is incompatible with Python string formatting, so we have to do this awkward
            # NOTE manual formatting instead.
            neo4j_session.run(
                ingest_rule.replace("#RULE_TYPE#", rule_type_map[rule_type]),
                RuleId=ruleid,
                FromPort=from_port,
                ToPort=to_port,
                Protocol=protocol,
                GroupId=group_id,
                aws_update_tag=aws_update_tag,
            )

            neo4j_session.run(
                ingest_rule_group_pair,
                GroupId=group_id,
                RuleId=ruleid,
                aws_update_tag=aws_update_tag,
            )

            for ip_range in rule["IpRanges"]:
                range_id = ip_range["CidrIp"]
                neo4j_session.run(
                    ingest_range,
                    RangeId=range_id,
                    RuleId=ruleid,
                    aws_update_tag=aws_update_tag,
                )


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
    MERGE (instance:Instance:EC2Instance{instanceid: {InstanceId}})
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


def load_load_balancers(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
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

        neo4j_session.run(
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
            aws_update_tag=aws_update_tag,
        )

        if lb["Subnets"]:
            load_load_balancer_subnets(neo4j_session, load_balancer_id, lb["Subnets"], aws_update_tag)

        if lb["SecurityGroups"]:
            for group in lb["SecurityGroups"]:
                neo4j_session.run(
                    ingest_load_balancer_security_group,
                    ID=load_balancer_id,
                    GROUP_ID=str(group),
                    aws_update_tag=aws_update_tag,
                )

        if lb["SourceSecurityGroup"]:
            source_group = lb["SourceSecurityGroup"]
            neo4j_session.run(
                ingest_load_balancersource_security_group,
                ID=load_balancer_id,
                GROUP_NAME=source_group["GroupName"],
                aws_update_tag=aws_update_tag,
            )

        if lb["Instances"]:
            for instance in lb["Instances"]:
                neo4j_session.run(
                    ingest_instances,
                    ID=load_balancer_id,
                    INSTANCE_ID=instance["InstanceId"],
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    aws_update_tag=aws_update_tag,
                )

        if lb["ListenerDescriptions"]:
            load_load_balancer_listeners(neo4j_session, load_balancer_id, lb["ListenerDescriptions"], aws_update_tag)


def load_load_balancer_subnets(neo4j_session, load_balancer_id, subnets_data, aws_update_tag):
    ingest_load_balancer_subnet = """
    MATCH (elb:LoadBalancer{id: {ID}}), (subnet:EC2Subnet{subnetid: {SUBNET_ID}})
    MERGE (elb)-[r:SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for subnet_id in subnets_data:
        neo4j_session.run(
            ingest_load_balancer_subnet,
            ID=load_balancer_id,
            SUBNET_ID=subnet_id,
            aws_update_tag=aws_update_tag,
        )


def load_load_balancer_listeners(neo4j_session, load_balancer_id, listener_data, aws_update_tag):
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

    neo4j_session.run(
        ingest_listener,
        LoadBalancerId=load_balancer_id,
        Listeners=listener_data,
        aws_update_tag=aws_update_tag,
    )


def load_ec2_vpc_peering(neo4j_session, data, aws_update_tag):
    # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpc-peering-connections.html
    # {
    #     "VpcPeeringConnections": [
    #         {
    #             "Status": {
    #                 "Message": "Active",
    #                 "Code": "active"
    #             },
    #             "Tags": [
    #                 {
    #                     "Value": "Peering-1",
    #                     "Key": "Name"
    #                 }
    #             ],
    #             "AccepterVpcInfo": {
    #                 "OwnerId": "111122223333",
    #                 "VpcId": "vpc-1a2b3c4d",
    #                 "CidrBlock": "10.0.1.0/28"
    #             },
    #             "VpcPeeringConnectionId": "pcx-11122233",
    #             "RequesterVpcInfo": {
    #                 "PeeringOptions": {
    #                     "AllowEgressFromLocalVpcToRemoteClassicLink": false,
    #                     "AllowEgressFromLocalClassicLinkToRemoteVpc": false
    #                 },
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-123abc45",
    #                 "CidrBlock": "192.168.0.0/16"
    #             }
    #         },
    #         {
    #             "Status": {
    #                 "Message": "Pending Acceptance by 444455556666",
    #                 "Code": "pending-acceptance"
    #             },
    #             "Tags": [],
    #             "RequesterVpcInfo": {
    #                 "PeeringOptions": {
    #                     "AllowEgressFromLocalVpcToRemoteClassicLink": false,
    #                     "AllowEgressFromLocalClassicLinkToRemoteVpc": false
    #                 },
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-11aa22bb",
    #                 "CidrBlock": "10.0.0.0/28"
    #             },
    #             "VpcPeeringConnectionId": "pcx-abababab",
    #             "ExpirationTime": "2014-04-03T09:12:43.000Z",
    #             "AccepterVpcInfo": {
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-33cc44dd"
    #             }
    #         }
    #     ]
    # }

    # We assume the accept data is already in the graph since we run after all AWS account in scope
    # We don't assume the requestor data is in the graph as it can be a foreign AWS account
    # IPV6 peering is not supported, we default to AWSIpv4CidrBlock
    #
    # We skip the region field here as we may not know which one it's related to in case of foreign VPC
    ingest_peering = """
    MATCH (accepter_block:AWSIpv4CidrBlock{id: {AccepterVpcId} + '|' + {AccepterCidrBlock}})
    WITH accepter_block
    MERGE (requestor_account:AWSAccount{id: {RequesterOwnerId}})
    ON CREATE SET requestor_account.firstseen = timestamp(), requestor_account.foreign = true
    SET requestor_account.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_account
    MERGE (requestor_vpc:AWSVpc{id: {RequestorVpcId}})
    ON CREATE SET requestor_vpc.firstseen = timestamp(), requestor_vpc.vpcid = {RequestorVpcId}
    SET requestor_vpc.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_account, requestor_vpc
    MERGE (requestor_account)-[resource:RESOURCE]->(requestor_vpc)
    ON CREATE SET resource.firstseen = timestamp()
    SET resource.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_vpc
    MERGE (requestor_block:AWSCidrBlock:AWSIpv4CidrBlock{id: {RequestorVpcId} + '|' + {RequestorVpcCidrBlock}})
    ON CREATE SET requestor_block.firstseen = timestamp(), requestor_block.cidr_block = {RequestorVpcCidrBlock}
    SET requestor_block.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_vpc, requestor_block
    MERGE (requestor_vpc)-[r:BLOCK_ASSOCIATION]->(requestor_block)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_block
    MERGE (accepter_block)<-[r2:VPC_PEERING]->(requestor_block)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.status_code = {StatusCode},
    r2.status_message = {StatusMessage},
    r2.connection_id = {ConnectionId},
    r2.expiration_time = {ExpirationTime},
    r2.lastupdated = {aws_update_tag}
    """

    ingest_peering_block = """
    MATCH (accepter_block:AWSIpv4CidrBlock{id: {AccepterVpcId} + '|' + {AccepterCidrBlock}}),
    (requestor_block:AWSCidrBlock:AWSIpv4CidrBlock{id: {RequestorVpcId} + '|' + {RequestorVpcCidrBlock}})
    MERGE (accepter_block)<-[r:VPC_PEERING]->(requestor_block)
    ON CREATE SET r.firstseen = timestamp()
    SET r.status_code = {StatusCode},
    r.status_message = {StatusMessage},
    r.connection_id = {ConnectionId},
    r.expiration_time = {ExpirationTime},
    r.lastupdated = {aws_update_tag}
    """
    for peering in data['VpcPeeringConnections']:
        if peering["Status"]["Code"] == "active":
            neo4j_session.run(
                ingest_peering,
                AccepterVpcId=peering["AccepterVpcInfo"]["VpcId"],
                AccepterCidrBlock=peering["AccepterVpcInfo"]["CidrBlock"],
                RequesterOwnerId=peering["RequesterVpcInfo"]["OwnerId"],
                RequestorVpcId=peering["RequesterVpcInfo"]["VpcId"],
                RequestorVpcCidrBlock=peering["RequesterVpcInfo"]["CidrBlock"],
                StatusCode=peering["Status"]["Code"],
                StatusMessage=peering["Status"]["Message"],
                ConnectionId=peering["VpcPeeringConnectionId"],
                ExpirationTime=peering.get("ExpirationTime", None),
                aws_update_tag=aws_update_tag,
            )

            for accepter_block in peering["AccepterVpcInfo"].get("CidrBlockSet", []):
                for requestor_block in peering["RequesterVpcInfo"].get("CidrBlockSet", []):
                    neo4j_session.run(
                        ingest_peering_block,
                        AccepterVpcId=peering["AccepterVpcInfo"]["VpcId"],
                        AccepterCidrBlock=accepter_block["CidrBlock"],
                        RequestorVpcId=peering["RequesterVpcInfo"]["VpcId"],
                        RequestorVpcCidrBlock=requestor_block["CidrBlock"],
                        StatusCode=peering["Status"]["Code"],
                        StatusMessage=peering["Status"]["Message"],
                        ConnectionId=peering["VpcPeeringConnectionId"],
                        ExpirationTime=peering.get("ExpirationTime", None),
                        aws_update_tag=aws_update_tag,
                    )


def load_ec2_vpcs(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html
    # {
    #     "Vpcs": [
    #         {
    #             "VpcId": "vpc-a01106c2",
    #             "InstanceTenancy": "default",
    #             "Tags": [
    #                 {
    #                     "Value": "MyVPC",
    #                     "Key": "Name"
    #                 }
    #             ],
    #             "CidrBlockAssociations": [
    #                 {
    #                     "AssociationId": "vpc-cidr-assoc-a26a41ca",
    #                     "CidrBlock": "10.0.0.0/16",
    #                     "CidrBlockState": {
    #                         "State": "associated"
    #                     }
    #                 }
    #             ],
    #             "State": "available",
    #             "DhcpOptionsId": "dopt-7a8b9c2d",
    #             "CidrBlock": "10.0.0.0/16",
    #             "IsDefault": false
    #         }
    #     ]
    # }

    ingest_vpc = """
    MERGE (new_vpc:AWSVpc{id: {VpcId}})
    ON CREATE SET new_vpc.firstseen = timestamp(), new_vpc.vpcid ={VpcId}
    SET new_vpc.instance_tenancy = {InstanceTenancy},
    new_vpc.state = {State},
    new_vpc.is_default = {IsDefault},
    new_vpc.primary_cidr_block = {PrimaryCIDRBlock},
    new_vpc.dhcp_options_id = {DhcpOptionsId},
    new_vpc.region = {Region},
    new_vpc.lastupdated = {aws_update_tag}
    WITH new_vpc
    MATCH (awsAccount:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (awsAccount)-[r:RESOURCE]->(new_vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}"""

    for vpc in data['Vpcs']:
        vpc_id = vpc["VpcId"]  # fail if not present

        neo4j_session.run(
            ingest_vpc,
            VpcId=vpc_id,
            InstanceTenancy=vpc.get("InstanceTenancy", None),
            State=vpc.get("State", None),
            IsDefault=vpc.get("IsDefault", None),
            PrimaryCIDRBlock=vpc.get("CidrBlock", None),
            DhcpOptionsId=vpc.get("DhcpOptionsId", None),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        load_cidr_association_set(
            neo4j_session,
            vpc_id=vpc_id,
            block_type="ipv4",
            vpc_data=vpc,
            aws_update_tag=aws_update_tag,
        )

        load_cidr_association_set(
            neo4j_session,
            vpc_id=vpc_id,
            block_type="ipv6",
            vpc_data=vpc,
            aws_update_tag=aws_update_tag,
        )


def _get_cidr_association_statement(block_type):
    ingest_cidr = """
    MATCH (vpc:AWSVpc{id: {VpcId}})
    WITH vpc
    UNWIND {CidrBlock} as block_data
        MERGE (new_block:#BLOCK_TYPE#{id: {VpcId} + '|' + block_data.#BLOCK_CIDR#})
        ON CREATE SET new_block.firstseen = timestamp()
        SET new_block.association_id = block_data.AssociationId,
        new_block.cidr_block = block_data.#BLOCK_CIDR#,
        new_block.block_state = block_data.#STATE_NAME#.State,
        new_block.block_state_message = block_data.#STATE_NAME#.StatusMessage,
        new_block.lastupdated = {aws_update_tag}
        WITH vpc, new_block
        MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(new_block)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}"""

    BLOCK_CIDR = "CidrBlock"
    STATE_NAME = "CidrBlockState"

    # base label type. We add the AWS ipv4 or 6 depending on block type
    BLOCK_TYPE = "AWSCidrBlock"

    if block_type == "ipv6":
        BLOCK_CIDR = "Ipv6" + BLOCK_CIDR
        STATE_NAME = "Ipv6" + STATE_NAME
        BLOCK_TYPE = BLOCK_TYPE + ":AWSIpv6CidrBlock"
    elif block_type == "ipv4":
        BLOCK_TYPE = BLOCK_TYPE + ":AWSIpv4CidrBlock"
    else:
        raise ValueError(f"Unsupported block type specified - {block_type}")

    return ingest_cidr.replace("#BLOCK_CIDR#", BLOCK_CIDR) \
        .replace("#STATE_NAME#", STATE_NAME) \
        .replace("#BLOCK_TYPE#", BLOCK_TYPE)


def load_cidr_association_set(neo4j_session, vpc_id, vpc_data, block_type, aws_update_tag):
    ingest_statement = _get_cidr_association_statement(block_type)

    if block_type == "ipv6":
        data = vpc_data.get("Ipv6CidrBlockAssociationSet", [])
    else:
        data = vpc_data.get("CidrBlockAssociationSet", [])

    neo4j_session.run(
        ingest_statement,
        VpcId=vpc_id,
        CidrBlock=data,
        aws_update_tag=aws_update_tag,
    )


def cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters):
    run_cleanup_job(
        'aws_import_ec2_security_groupinfo_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def cleanup_ec2_key_pairs(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_key_pairs_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters):
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


def cleanup_load_balancers(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_ingest_load_balancers_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_ec2_vpcs(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_vpc_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_ec2_vpc_peering(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_vpc_peering_cleanup.json', neo4j_session, common_job_parameters)


def sync_ec2_security_groupinfo(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 security groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_security_group_data(boto3_session, region)
        load_ec2_security_groupinfo(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters)


def sync_ec2_key_pairs(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_key_pairs(boto3_session, region)
        load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)


def sync_ec2_instances(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_instances(boto3_session, region)
        load_ec2_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_instances(neo4j_session, common_job_parameters)


def sync_ec2_auto_scaling_groups(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_auto_scaling_groups(boto3_session, region)
        load_ec2_auto_scaling_groups(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters)


def sync_load_balancers(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 load balancers for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_loadbalancer_data(boto3_session, region)
        load_load_balancers(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_load_balancers(neo4j_session, common_job_parameters)


def sync_vpc(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.debug("Syncing EC2 VPC for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_vpcs(boto3_session, region)
        load_ec2_vpcs(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_vpcs(neo4j_session, common_job_parameters)


def sync_vpc_peering(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 VPC peering for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_vpc_peering(boto3_session, region)
        load_ec2_vpc_peering(neo4j_session, data, aws_update_tag)
    cleanup_ec2_vpc_peering(neo4j_session, common_job_parameters)


def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    logger.info("Syncing EC2 for account '%s'.", account_id)
    sync_vpc(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_security_groupinfo(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_key_pairs(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_instances(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_auto_scaling_groups(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_load_balancers(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_vpc_peering(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

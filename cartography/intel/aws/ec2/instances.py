import logging
import time
from datetime import datetime
from typing import Any
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
def get_ec2_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_instances')
    reservations: List[Dict] = []
    for page in paginator.paginate():
        reservations.extend(page['Reservations'])
    return reservations


def _load_ec2_instance_net_if_tx(
        tx: neo4j.Transaction,
        instance_data: Dict[str, Any],
        update_tag: int,
) -> None:
    query = """
    MATCH (instance:EC2Instance{instanceid: $InstanceId})
    UNWIND $Interfaces as interface
        MERGE (nic:NetworkInterface{id: interface.NetworkInterfaceId})
        ON CREATE SET nic.firstseen = timestamp()
        SET nic.status = interface.Status,
        nic.mac_address = interface.MacAddress,
        nic.description = interface.Description,
        nic.private_dns_name = interface.PrivateDnsName,
        nic.private_ip_address = interface.PrivateIpAddress,
        nic.lastupdated = $update_tag

        MERGE (instance)-[r:NETWORK_INTERFACE]->(nic)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag

        WITH nic, interface
        WHERE interface.SubnetId IS NOT NULL
        MERGE (subnet:EC2Subnet{subnetid: interface.SubnetId})
        ON CREATE SET subnet.firstseen = timestamp()
        SET subnet.lastupdated = $update_tag

        MERGE (nic)-[r:PART_OF_SUBNET]->(subnet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag

        WITH nic, interface
        UNWIND interface.Groups as group
            MATCH (ec2group:EC2SecurityGroup{groupid: group.GroupId})
            MERGE (nic)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(ec2group)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        Interfaces=instance_data['NetworkInterfaces'],
        InstanceId=instance_data['InstanceId'],
        update_tag=update_tag,
    )


@timeit
def load_ec2_instance_network_interfaces(neo4j_session: neo4j.Session, instance_data: Dict, update_tag: int) -> None:
    neo4j_session.write_transaction(_load_ec2_instance_net_if_tx, instance_data, update_tag)


def _load_ec2_reservation_tx(
        tx: neo4j.Transaction,
        reservation_id: str,
        reservation: Dict[str, Any],
        current_aws_account_id: str,
        region: str,
        update_tag: int,
) -> None:
    query = """
        MERGE (reservation:EC2Reservation{reservationid: $ReservationId})
        ON CREATE SET reservation.firstseen = timestamp()
        SET reservation.ownerid = $OwnerId,
            reservation.requesterid = $RequesterId,
            reservation.region = $Region,
            reservation.lastupdated = $update_tag
        WITH reservation
        MATCH (awsAccount:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (awsAccount)-[r:RESOURCE]->(reservation)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        ReservationId=reservation_id,
        OwnerId=reservation.get("OwnerId"),
        RequesterId=reservation.get("RequesterId"),
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


def _load_ec2_instance_tx(
        tx: neo4j.Transaction,
        instanceid: str,
        instance: Dict[str, Any],
        reservation_id: str,
        monitoring_state: str,
        launch_time: datetime,
        launch_time_unix: str,
        instance_state: str,
        current_aws_account_id: str,
        region: str,
        update_tag: int,
) -> None:
    query = """
        MERGE (instance:Instance:EC2Instance{id: $InstanceId})
        ON CREATE SET instance.firstseen = timestamp()
        SET instance.instanceid = $InstanceId,
            instance.publicdnsname = $PublicDnsName,
            instance.privateipaddress = $PrivateIpAddress,
            instance.publicipaddress = $PublicIpAddress,
            instance.imageid = $ImageId,
            instance.instancetype = $InstanceType,
            instance.monitoringstate = $MonitoringState,
            instance.state = $State,
            instance.launchtime = $LaunchTime,
            instance.launchtimeunix = $LaunchTimeUnix,
            instance.region = $Region,
            instance.lastupdated = $update_tag,
            instance.iaminstanceprofile = $IamInstanceProfile,
            instance.availabilityzone = $AvailabilityZone,
            instance.tenancy = $Tenancy,
            instance.hostresourcegrouparn = $HostResourceGroupArn,
            instance.platform = $Platform,
            instance.architecture = $Architecture,
            instance.ebsoptimized = $EbsOptimized,
            instance.bootmode = $BootMode,
            instance.instancelifecycle = $InstanceLifecycle,
            instance.hibernationoptions = $HibernationOptions
        WITH instance
        MATCH (rez:EC2Reservation{reservationid: $ReservationId})
        MERGE (instance)-[r:MEMBER_OF_EC2_RESERVATION]->(rez)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH instance
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(instance)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        InstanceId=instanceid,
        PublicDnsName=instance.get("PublicDnsName"),
        PublicIpAddress=instance.get("PublicIpAddress"),
        PrivateIpAddress=instance.get("PrivateIpAddress"),
        ImageId=instance.get("ImageId"),
        InstanceType=instance.get("InstanceType"),
        IamInstanceProfile=instance.get("IamInstanceProfile", {}).get("Arn"),
        ReservationId=reservation_id,
        MonitoringState=monitoring_state,
        LaunchTime=str(launch_time),
        LaunchTimeUnix=launch_time_unix,
        State=instance_state,
        AvailabilityZone=instance.get("Placement", {}).get("AvailabilityZone"),
        Tenancy=instance.get("Placement", {}).get("Tenancy"),
        HostResourceGroupArn=instance.get("Placement", {}).get("HostResourceGroupArn"),
        Platform=instance.get("Platform"),
        Architecture=instance.get("Architecture"),
        EbsOptimized=instance.get("EbsOptimized"),
        BootMode=instance.get("BootMode"),
        InstanceLifecycle=instance.get("InstanceLifecycle"),
        HibernationOptions=instance.get("HibernationOptions", {}).get("Configured"),
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


def _load_ec2_subnet_tx(tx: neo4j.Transaction, instanceid: str, subnet_id: str, region: str, update_tag: int) -> None:
    query = """
        MATCH (instance:EC2Instance{id: $InstanceId})
        MERGE (subnet:EC2Subnet{subnetid: $SubnetId})
        ON CREATE SET subnet.firstseen = timestamp()
        SET subnet.region = $Region,
        subnet.lastupdated = $update_tag
        MERGE (instance)-[r:PART_OF_SUBNET]->(subnet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        InstanceId=instanceid,
        SubnetId=subnet_id,
        Region=region,
        update_tag=update_tag,
    )


def _load_ec2_keypairs_tx(
        tx: neo4j.Transaction,
        key_pair_arn: str,
        key_name: str,
        region: str,
        instanceid: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    query = """
        MERGE (keypair:KeyPair:EC2KeyPair{arn: $KeyPairARN, id: $KeyPairARN})
        ON CREATE SET keypair.firstseen = timestamp()
        SET keypair.keyname = $KeyName, keypair.region = $Region, keypair.lastupdated = $update_tag
        WITH keypair
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(keypair)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        with keypair
        MATCH (instance:EC2Instance{instanceid: $InstanceId})
        MERGE (instance)<-[r:SSH_LOGIN_TO]-(keypair)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        KeyPairARN=key_pair_arn,
        KeyName=key_name,
        Region=region,
        InstanceId=instanceid,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def _load_ec2_security_groups_tx(
        tx: neo4j.Transaction,
        group_id: str,
        group: Dict[str, Any],
        instanceid: str,
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    query = """
        MERGE (group:EC2SecurityGroup{id: $GroupId})
        ON CREATE SET group.firstseen = timestamp(), group.groupid = $GroupId
        SET group.name = $GroupName, group.region = $Region, group.lastupdated = $update_tag
        WITH group
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH group
        MATCH (instance:EC2Instance{instanceid: $InstanceId})
        MERGE (instance)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        GroupId=group_id,
        GroupName=group.get("GroupName"),
        InstanceId=instanceid,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


@timeit
def load_ec2_instances(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
        update_tag: int,
) -> None:
    for reservation in data:
        reservation_id = reservation["ReservationId"]
        neo4j_session.write_transaction(
            _load_ec2_reservation_tx,
            reservation_id,
            reservation,
            current_aws_account_id,
            region,
            update_tag,
        )

        for instance in reservation["Instances"]:
            instanceid = instance["InstanceId"]

            monitoring_state = instance.get("Monitoring", {}).get("State")

            instance_state = instance.get("State", {}).get("Name")

            # NOTE this is a hack because we're using a version of Neo4j that doesn't support temporal data types
            launch_time = instance.get("LaunchTime")
            if launch_time:
                launch_time_unix = str(time.mktime(launch_time.timetuple()))
            else:
                launch_time_unix = ""

            neo4j_session.write_transaction(
                _load_ec2_instance_tx,
                instanceid,
                instance,
                reservation_id,
                monitoring_state,
                launch_time,
                launch_time_unix,
                instance_state,
                current_aws_account_id,
                region,
                update_tag,
            )

            # SubnetId can return None intermittently so attach only if non-None.
            subnet_id = instance.get('SubnetId')
            if subnet_id:
                neo4j_session.write_transaction(_load_ec2_subnet_tx, instanceid, subnet_id, region, update_tag)

            if instance.get("KeyName"):
                key_name = instance["KeyName"]
                key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'
                neo4j_session.write_transaction(
                    _load_ec2_keypairs_tx,
                    key_pair_arn,
                    key_name,
                    region,
                    instanceid,
                    current_aws_account_id,
                    update_tag,
                )

            if instance.get("SecurityGroups"):
                for group in instance["SecurityGroups"]:
                    group_id = group["GroupId"]
                    neo4j_session.write_transaction(
                        _load_ec2_security_groups_tx,
                        group_id,
                        group,
                        instanceid,
                        region,
                        current_aws_account_id,
                        update_tag,
                    )

            load_ec2_instance_network_interfaces(neo4j_session, instance, update_tag)
            instance_ebs_volumes_list = get_ec2_instance_ebs_volumes(instance)
            load_ec2_instance_ebs_volumes(neo4j_session, instance_ebs_volumes_list, current_aws_account_id, update_tag)


@timeit
def get_ec2_instance_ebs_volumes(instance: Dict) -> List[Dict]:
    instance_ebs_volumes_list: List[Dict] = []
    if 'BlockDeviceMappings' in instance and len(instance['BlockDeviceMappings']) > 0:
        for mapping in instance['BlockDeviceMappings']:
            if 'VolumeId' in mapping['Ebs']:
                mapping['InstanceId'] = instance["InstanceId"]
                instance_ebs_volumes_list.append(mapping)
    return instance_ebs_volumes_list


def _load_ec2_instance_ebs_tx(
        tx: neo4j.Transaction,
        ebs_data: List[Dict[str, Any]],
        update_tag: int,
        current_aws_account_id: str,
) -> None:
    query = """
        UNWIND $ebs_mappings_list as em
            MERGE (vol:EBSVolume{id: em.Ebs.VolumeId})
            ON CREATE SET vol.firstseen = timestamp()
            SET vol.lastupdated = $update_tag,
                vol.deleteontermination = em.Ebs.DeleteOnTermination,
                vol.snapshotid = vol.SnapshotId
            WITH vol, em
            MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (aa)-[r:RESOURCE]->(vol)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
            WITH vol, em
            MATCH (instance:EC2Instance{instanceid: em.InstanceId})
            MERGE (vol)-[r:ATTACHED_TO]->(instance)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        ebs_mappings_list=ebs_data,
        update_tag=update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    )


@timeit
def load_ec2_instance_ebs_volumes(
        neo4j_session: neo4j.Session, ebs_data: List[Dict[str, Any]], current_aws_account_id: str, update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_ec2_instance_ebs_tx,
        ebs_data,
        update_tag,
        current_aws_account_id,
    )


@timeit
def cleanup_ec2_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_ec2_instances(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_instances(boto3_session, region)
        load_ec2_instances(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_instances(neo4j_session, common_job_parameters)

import math
import logging
import time
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from botocore.exceptions import ClientError
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_ec2_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    reservations = []
    try:
        paginator = client.get_paginator('describe_instances')
        for page in paginator.paginate():
            reservations.extend(page['Reservations'])
        for reservation in reservations:
            reservation['region'] = region

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                f'ec2:describe_security_groups failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise

    return reservations


def load_ec2_instance_network_interfaces(
    neo4j_session: neo4j.Session,
    network_interfaces: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        load_ec2_instance_network_interfaces_tx,
        network_interfaces,
        current_aws_account_id,
        update_tag,
    )


def load_ec2_instance_network_interfaces_tx(
        tx: neo4j.Transaction,
        network_interfaces: List[Dict[str, Any]],
        current_aws_account_id: int,
        update_tag: int,
) -> None:
    query = """
        UNWIND $NetworkInterfaces as interface
            MERGE (nic:NetworkInterface{id: interface.NetworkInterfaceId})
            ON CREATE SET nic.firstseen = timestamp()
            SET nic.status = interface.Status,
            nic.region = interface.Region,
            nic.mac_address = interface.MacAddress,
            nic.description = interface.Description,
            nic.private_dns_name = interface.PrivateDnsName,
            nic.private_ip_address = interface.PrivateIpAddress,
            nic.arn = interface.Arn,
            nic.lastupdated = $update_tag
            
            WITH nic, interface
            MATCH (instance:EC2Instance{instanceid: interface.InstanceId})
            MERGE (instance)-[r:NETWORK_INTERFACE]->(nic)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag

            WITH nic, interface
            WHERE interface.SubnetId IS NOT NULL
            MERGE (subnet:EC2Subnet{subnetid: interface.SubnetId})
            ON CREATE SET subnet.firstseen = timestamp()
            SET subnet.lastupdated = $update_tag

            WITH nic, interface
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
        NetworkInterfaces=network_interfaces,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def _load_ec2_reservations(
    neo4j_session: neo4j.Session,
    reservations: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_ec2_reservation_tx,
        reservations,
        current_aws_account_id,
        update_tag,
    )


def _load_ec2_reservation_tx(
        tx: neo4j.Transaction,
        reservations: List[Dict[str, Any]],
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    query = """
        UNWIND $Reservations as reservation
            MERGE (rsv:EC2Reservation{reservationid: reservation.ReservationId})
            ON CREATE SET rsv.firstseen = timestamp()
            SET rsv.ownerid = reservation.OwnerId,
                rsv.requesterid = reservation.RequesterId,
                rsv.region = reservation.region,
                rsv.lastupdated = $update_tag
            WITH rsv
            MATCH (awsAccount:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (awsAccount)-[r:RESOURCE]->(rsv)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        Reservations=reservations,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def _load_ec2_instances(
    neo4j_session: neo4j.Session,
    instances: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    iteration_size = 200
    total_items = len(instances)
    total_iterations = math.ceil(len(instances) / iteration_size)
    logger.info(f"Total EC2 Instances: {total_items}")

    for counter in range(0, total_iterations):
        start = iteration_size * (counter)

        if (start + iteration_size) >= total_items:
            end = total_items
            paginated_instances = instances[start:]

        else:
            end = start + iteration_size
            paginated_instances = instances[start:end]

        neo4j_session.write_transaction(
            _load_ec2_instances_tx,
            paginated_instances,
            current_aws_account_id,
            update_tag,
        )

        logger.info(f"Iteration {counter + 1} of {total_iterations}. {start} - {end} - {len(paginated_instances)}")


def _load_ec2_instances_tx(
        tx: neo4j.Transaction,
        instances: List[Dict[str, Any]],
        current_aws_account_id: str,
        update_tag: str,
) -> None:
    query = """
        UNWIND $Instances as inst
            MERGE (instance:Instance:EC2Instance{id: inst.InstanceId})
            ON CREATE SET instance.firstseen = timestamp()
            SET instance.instanceid = inst.InstanceId,
                instance.publicdnsname = inst.PublicDnsName,
                instance.privatednsname = inst.PrivateDnsName,
                instance.privateipaddress = inst.PrivateIpAddress,
                instance.publicipaddress = inst.PublicIpAddress,
                instance.imageid = inst.ImageId,
                instance.instancetype = inst.InstanceType,
                instance.monitoringstate = inst.Monitoring.State,
                instance.state = inst.State.Name,
                instance.launchtime = inst.LaunchTime,
                instance.launchtimeunix = inst.LaunchTimeUnix,
                instance.instancelifecycle = inst.InstanceLifecycle,
                instance.region = inst.region,
                instance.lastupdated = $update_tag,
                instance.availabilityzone = inst.Placement.AvailabilityZone,
                instance.tenancy = inst.Placement.Tenancy,
                instance.hostresourcegrouparn = inst.Placement.HostResourceGroupArn,
                instance.platform = inst.Platform,
                instance.architecture = inst.Architecture,
                instance.ebsoptimized = inst.EbsOptimized,
                instance.bootmode = inst.BootMode,
                instance.instancelifecycle = inst.InstanceLifecycle,
                instance.hibernationoptions = inst.HibernationOptions.Configured,
                instance.consolelink = inst.consolelink,
                instance.arn = inst.InstanceArn
            WITH instance, inst
            MERGE (profile:AWSInstanceProfile{arn: inst.IamInstanceProfile.Arn})
            ON CREATE SET profile.id = inst.IamInstanceProfile.Id, profile.firstseen = timestamp()
            SET profile.lastupdated = $update_tag
            WITH instance, inst, profile
            MERGE (instance)-[rel:PROFILE]->(profile)
            ON CREATE SET rel.firstseen = timestamp()
            SET rel.lastupdated - $update_tag
            WITH instance, inst
            MATCH (rez:EC2Reservation{reservationid: inst.ReservationId})
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
        Instances=instances,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def _load_ec2_subnet_tx(tx: neo4j.Transaction, instanceid: str, subnet_id: str, region: str, update_tag: int) -> None:
    query = """
        MERGE (instance:Instance:EC2Instance{id: $InstanceId})
        ON CREATE SET instance.firstseen = timestamp()
        SET instance.region = $Region,
        instance.lastupdated = $update_tag
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


def _load_ec2_key_pairs(
    neo4j_session: neo4j.Session,
    key_pairs: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_ec2_key_pairs_tx,
        key_pairs,
        current_aws_account_id,
        update_tag,
    )


def _load_ec2_key_pairs_tx(
        tx: neo4j.Transaction,
        key_pairs: List[Dict[str, Any]],
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    query = """
        UNWIND $KeyPairs as key_pair
            MERGE (keypair:KeyPair:EC2KeyPair{arn: key_pair.KeyARN, id: key_pair.KeyARN})
            ON CREATE SET keypair.firstseen = timestamp()
            SET keypair.keyname = key_pair.KeyName, keypair.region = key_pair.Region, keypair.lastupdated = $update_tag
            WITH keypair, key_pair
            MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (aa)-[r:RESOURCE]->(keypair)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
            with keypair, key_pair
            MATCH (instance:EC2Instance{instanceid: key_pair.InstanceId})
            MERGE (instance)<-[r:SSH_LOGIN_TO]-(keypair)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        KeyPairs=key_pairs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def _load_ec2_security_groups(
    neo4j_session: neo4j.Session,
    security_groups: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_ec2_security_groups_tx,
        security_groups,
        current_aws_account_id,
        update_tag,
    )


def _load_ec2_security_groups_tx(
        tx: neo4j.Transaction,
        security_groups: List[Dict[str, Any]],
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    query = """
        UNWIND $SecurityGroups as sg
            MERGE (group:EC2SecurityGroup{id: sg.GroupId})
            ON CREATE SET group.firstseen = timestamp(), group.groupid = sg.GroupId
            SET group.name = sg.GroupName, group.region = sg.Region, group.lastupdated = $update_tag
            WITH group, sg
            MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (aa)-[r:RESOURCE]->(group)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
            WITH group, sg
            MATCH (instance:EC2Instance{instanceid: sg.InstanceId})
            MERGE (instance)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        SecurityGroups=security_groups,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


@timeit
def load_ec2_instances(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str,
        update_tag: int,
) -> None:
    reservations = []
    instances = []
    key_pairs = []
    security_groups = []
    network_interfaces = []
    ebs_volumes = []

    for reservation in data:
        region = reservation.get('region', '')
        reservation['region'] = region
        reservation_id = reservation["ReservationId"]
        reservations.append(reservation)

        for instance in reservation["Instances"]:
            instanceid = instance["InstanceId"]
            instance["region"] = region
            instance['InstanceArn'] = f"arn:aws:ec2:{region}:{current_aws_account_id}:instance/{instanceid}"
            instance['consolelink'] = aws_console_link.get_console_link(arn=instance['InstanceArn'])

            # NOTE this is a hack because we're using a version of Neo4j that doesn't support temporal data types
            launch_time = instance.get("LaunchTime")
            if launch_time:
                launch_time_unix = str(time.mktime(launch_time.timetuple()))
            else:
                launch_time_unix = ""

            instance['LaunchTimeUnix'] = launch_time_unix
            instance['ReservationId'] = reservation_id
            instances.append(instance)

            # SubnetId can return None intermittently so attach only if non-None.
            subnet_id = instance.get('SubnetId')
            if subnet_id:
                neo4j_session.write_transaction(_load_ec2_subnet_tx, instanceid, subnet_id, region, update_tag)

            if instance.get("KeyName"):
                key_name = instance["KeyName"]
                key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'

                key_pairs.append({
                    "KeyARN": key_pair_arn,
                    "KeyName": instance["KeyName"],
                    "InstanceId": instance["InstanceId"],
                    "Region": region,
                })

            if instance.get("SecurityGroups"):
                for group in instance["SecurityGroups"]:
                    security_groups.append({
                        "GroupId": group["GroupId"],
                        "GroupName": group["GroupName"],
                        "InstanceId": instance["InstanceId"],
                        "Region": region,
                    })

            if instance.get("NetworkInterfaces"):
                for interface in instance['NetworkInterfaces']:
                    network_interfaces.append({
                        "NetworkInterfaceId": interface.get("NetworkInterfaceId"),
                        "Status": interface.get("Status"),
                        "MacAddress": interface.get("MacAddress"),
                        "Description": interface.get("Description"),
                        "PrivateDnsName": interface.get("PrivateDnsName"),
                        "PrivateIpAddress": interface.get("PrivateIpAddress"),
                        "SubnetId": interface.get("SubnetId"),
                        "InstanceId": instance["InstanceId"],
                        "Groups": interface.get("Groups"),
                        "Region": region,
                        "Arn": f"arn:aws:ec2:{region}:{current_aws_account_id}:network-interface/{interface['NetworkInterfaceId']}"
                    })

            if instance.get("BlockDeviceMappings"):
                for ebs_volume in instance['BlockDeviceMappings']:
                    if 'VolumeId' in ebs_volume['Ebs']:
                        ebs_volumes.append({
                            "VolumeId": ebs_volume.get('Ebs', {}).get('VolumeId'),
                            "DeleteOnTermination": ebs_volume.get('Ebs', {}).get('DeleteOnTermination'),
                            "InstanceId": instance["InstanceId"],
                            "Region": region,
                        })

    _load_ec2_reservations(neo4j_session, reservations, current_aws_account_id, update_tag)

    _load_ec2_instances(neo4j_session, instances, current_aws_account_id, update_tag)

    _load_ec2_key_pairs(neo4j_session, key_pairs, current_aws_account_id, update_tag)

    _load_ec2_security_groups(neo4j_session, security_groups, current_aws_account_id, update_tag)

    load_ec2_instance_network_interfaces(neo4j_session, network_interfaces, current_aws_account_id, update_tag)

    sync_ec2_instance_ebs_volumes(neo4j_session, ebs_volumes, current_aws_account_id, update_tag)


@timeit
def sync_ec2_instance_ebs_volumes(
    neo4j_session: neo4j.Session,
    ebs_volumes: List[Dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        sync_ec2_instance_ebs_volumes_tx,
        ebs_volumes,
        current_aws_account_id,
        update_tag,
    )


def sync_ec2_instance_ebs_volumes_tx(
        tx: neo4j.Transaction,
        ebs_volumes: List[Dict[str, Any]],
        current_aws_account_id: str,
        update_tag: str,
) -> None:
    query = """
        UNWIND $EBSVolumes as volume
            MERGE (vol:EBSVolume{id: volume.VolumeId})
            ON CREATE SET vol.firstseen = timestamp()
            SET vol.lastupdated = $update_tag,
            vol.region = volume.Region,
            vol.deleteontermination = volume.DeleteOnTermination

            WITH vol, volume
            MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (aa)-[r:RESOURCE]->(vol)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag

            WITH vol, volume
            MATCH (instance:EC2Instance{instanceid: volume.InstanceId})
            MERGE (vol)-[r:ATTACHED_TO]->(instance)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        EBSVolumes=ebs_volumes,
        update_tag=update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    )


@timeit
def cleanup_ec2_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_ec2_instances(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 instances for account '%s', at %s.", current_aws_account_id, tic)

    data = []
    for region in regions:
        logger.info("Syncing EC2 instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_ec2_instances(boto3_session, region))

    logger.info(f"Total EC2 Reservations: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('ec2:instance', None):
        pageNo = common_job_parameters.get("pagination", {}).get("ec2:instance", {}).get("pageNo")
        pageSize = common_job_parameters.get("pagination", {}).get("ec2:instance", {}).get("pageSize")
        totalPages = len(data) / pageSize

        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)

        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for ec2:instance {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('ec2:instance', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('ec2:instance', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('ec2:instance', {})['pageSize']

        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]

        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['ec2:instance']['hasNextPage'] = has_next_page

    load_ec2_instances(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_ec2_instances(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 instances: {toc - tic:0.4f} seconds")

import logging
import re

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_network_interface_data(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_network_interfaces')
    subnets = []
    for page in paginator.paginate():
        subnets.extend(page['NetworkInterfaces'])
    return subnets


@timeit
def load_network_interfaces(neo4j_session, data, region, aws_account_id, aws_update_tag):
    """
    Creates (:NetworkInterface),
    (:NetworkInterface)-[:RESOURCE]->(:AWSAccount),
    (:NetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:EC2SecurityGroup),
    (:NetworkInterface)-[:PART_OF_SUBNET]->(:EC2Subnet),
    (:PrivateIpAddress),
    (:NetworkInterface)-[:PRIVATE_IP_ADDRESS]->(:PrivateIpAddress)
    """
    logger.debug("Loading %d network interfaces in %s.", len(data), region)
    ingest_network_interfaces = """
    UNWIND {network_interfaces} AS network_interface
        MERGE (netinf:NetworkInterface{id: network_interface.NetworkInterfaceId})
        ON CREATE SET netinf.firstseen = timestamp()
        SET netinf.lastupdated = {aws_update_tag},
            netinf.mac_address = network_interface.MacAddress,
            netinf.description = network_interface.Description,
            netinf.private_ip_address = network_interface.PrivateIpAddress,
            netinf.id = network_interface.NetworkInterfaceId,
            netinf.private_dns_name = network_interface.PrivateDnsName,
            netinf.status = network_interface.Status,
            netinf.subnetid = network_interface.SubnetId,
            netinf.interface_type = network_interface.InterfaceType,
            netinf.requester_managed = network_interface.RequesterManaged,
            netinf.source_dest_check = network_interface.SourceDestCheck,
            netinf.requester_id = network_interface.RequesterId,
            netinf.public_ip = network_interface.Association.PublicIp
        WITH network_interface, netinf

        UNWIND network_interface.PrivateIpAddresses AS private_ip_address
            MERGE (private_ip:EC2PrivateIp{id: network_interface.NetworkInterfaceId + ':'
                + private_ip_address.PrivateIpAddress})
            ON CREATE SET private_ip.firstseen = timestamp()
            SET private_ip.lastupdated = {aws_update_tag},
                private_ip.network_interface_id = network_interface.NetworkInterfaceId,
                private_ip.primary = private_ip_address.Primary,
                private_ip.private_ip_address = private_ip_address.PrivateIpAddress,
                private_ip.public_ip = private_ip_address.Association.PublicIp,
                private_ip.ip_owner_id = private_ip_address.Association.IpOwnerId

            MERGE (netinf)-[r:PRIVATE_IP_ADDRESS]->(private_ip)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {aws_update_tag}
        WITH network_interface, netinf

        UNWIND network_interface.Groups AS security_group
            MERGE (sg:EC2SecurityGroup{id: security_group.GroupId})
            ON CREATE SET sg.firstseen = timestamp()
            SET sg.lastupdated = {aws_update_tag}
            MERGE (netinf)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {aws_update_tag}
        WITH network_interface, netinf

        MERGE (acc:AWSAccount{id: {aws_account_id}})
        ON CREATE SET acc.firstseen = timestamp()
        SET acc.lastupdated = {aws_update_tag}
        MERGE (acc)-[r:RESOURCE]->(netinf)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        WITH network_interface, netinf

        MERGE (snet:EC2Subnet{subnetid: network_interface.SubnetId})
        ON CREATE SET snet.firstseen = timestamp()
        SET snet.lastupdated = {aws_update_tag}
        MERGE (netinf)-[r:PART_OF_SUBNET]->(snet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_network_interfaces, network_interfaces=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_network_interface_instance_relations(
    neo4j_session, instance_associations, region, aws_account_id, aws_update_tag,
):
    """
    Creates (:EC2Instance)-[:NETWORK_INTERFACE]->(:NetworkInterface)
    """
    ingest_network_interface_instance_relations = """
    UNWIND {instance_associations} AS instance_association
        MATCH (netinf:NetworkInterface{id: instance_association.netinf_id}),
            (instance:EC2Instance{id: instance_association.instance_id})
        MERGE (instance)-[r:NETWORK_INTERFACE]->(netinf)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("Attaching %d EC2 instances to network interfaces in %s.", len(instance_associations), region)
    neo4j_session.run(
        ingest_network_interface_instance_relations, instance_associations=instance_associations,
        aws_update_tag=aws_update_tag, region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_network_interface_elb_relations(neo4j_session, elb_associations, region, aws_account_id, aws_update_tag):
    """
    Creates (:LoadBalancer)-[:NETWORK_INTERFACE]->(:NetworkInterface)
    """
    ingest_network_interface_elb_relations = """
    UNWIND {elb_associations} AS elb_association
        MATCH (netinf:NetworkInterface{id: elb_association.netinf_id}),
            (elb:LoadBalancer{name: elb_association.elb_name})
        MERGE (elb)-[r:NETWORK_INTERFACE]->(netinf)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("Attaching %d ELBs to network interfaces in %s.", len(elb_associations), region)
    neo4j_session.run(
        ingest_network_interface_elb_relations, elb_associations=elb_associations,
        aws_update_tag=aws_update_tag, region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_network_interface_elbv2_relations(neo4j_session, elb_associations_v2, region, aws_account_id, aws_update_tag):
    """
    Creates (:LoadBalancerV2)-[:NETWORK_INTERFACE]->(:NetworkInterface)
    """
    ingest_network_interface_elb2_relations = """
    UNWIND {elb_associations} AS elb_association
        MATCH (netinf:NetworkInterface{id: elb_association.netinf_id}),
            (elb:LoadBalancerV2{id: elb_association.elb_id})
        MERGE (elb)-[r:NETWORK_INTERFACE]->(netinf)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("Attaching %d ELB V2s to network interfaces in %s.", len(elb_associations_v2), region)
    neo4j_session.run(
        ingest_network_interface_elb2_relations, elb_associations=elb_associations_v2,
        aws_update_tag=aws_update_tag, region=region, aws_account_id=aws_account_id,
    )


@timeit
def load_network_interface_instance_to_subnet_relations(neo4j_session, aws_update_tag):
    """
    Creates (:EC2Instance)-[:PART_OF_SUBNET]->(:EC2Subnet) if
    (:EC2Instance)--(:NetworkInterface)--(:EC2Subnet).
    """
    ingest_network_interface_instance_relations = """
    MATCH (i:EC2Instance)-[:NETWORK_INTERFACE]-(interface:NetworkInterface)-[:PART_OF_SUBNET]-(s:EC2Subnet)
    MERGE (i)-[r:PART_OF_SUBNET]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("-> Instance to subnet")
    neo4j_session.run(
        ingest_network_interface_instance_relations, aws_update_tag=aws_update_tag,
    )


@timeit
def load_network_interface_load_balancer_relations(neo4j_session, aws_update_tag):
    """
    Creates (:LoadBalancer)-[:PART_OF_SUBNET]->(:EC2Subnet) if
    (:LoadBalancer)--(:NetworkInterface)--(:EC2Subnet).
    """
    ingest_network_interface_loadbalancer_relations = """
    MATCH (i:LoadBalancer)-[:NETWORK_INTERFACE]-(interface:NetworkInterface)-[:PART_OF_SUBNET]-(s:EC2Subnet)
    MERGE (i)-[r:PART_OF_SUBNET]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("-> ELB to subnet")
    neo4j_session.run(
        ingest_network_interface_loadbalancer_relations, aws_update_tag=aws_update_tag,
    )


@timeit
def load_network_interface_load_balancer_v2_relations(neo4j_session, aws_update_tag):
    """
    Creates (:LoadBalancerV2)-[:PART_OF_SUBNET]->(:EC2Subnet) if
    (:LoadBalancerV2)--(:NetworkInterface)--(:EC2Subnet).
    """
    ingest_network_interface_loadbalancerv2_relations = """
    MATCH (i:LoadBalancerV2)-[:NETWORK_INTERFACE]-(interface:NetworkInterface)-[:PART_OF_SUBNET]-(s:EC2Subnet)
    MERGE (i)-[r:PART_OF_SUBNET]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("-> ELBv2 to subnet")
    neo4j_session.run(
        ingest_network_interface_loadbalancerv2_relations, aws_update_tag=aws_update_tag,
    )


@timeit
def load(neo4j_session, data, region, aws_account_id, aws_update_tag):
    elb_associations = []
    elb_associations_v2 = []
    instance_associations = []

    for network_interface in data:
        # https://aws.amazon.com/premiumsupport/knowledge-center/elb-find-load-balancer-IP/
        matchObj = re.match(r'^ELB (?:net|app)/([^\/]+)\/(.*)', network_interface.get('Description', ''))
        if matchObj:
            elb_associations_v2.append({
                'netinf_id': network_interface['NetworkInterfaceId'],
                'elb_id': '{}-{}.elb.{}.amazonaws.com'.format(matchObj[1], matchObj[2], region),
            })
        else:
            matchObj = re.match(r'^ELB (.*)', network_interface.get('Description', ''))
            if matchObj:
                elb_associations.append({
                    'netinf_id': network_interface['NetworkInterfaceId'],
                    'elb_name': matchObj[1],
                })

        if 'Attachment' in network_interface and 'InstanceId' in network_interface['Attachment']:
            instance_associations.append({
                'netinf_id': network_interface['NetworkInterfaceId'],
                'instance_id': network_interface['Attachment']['InstanceId'],
            })
    load_network_interfaces(neo4j_session, data, region, aws_account_id, aws_update_tag)
    load_network_interface_instance_relations(
        neo4j_session, instance_associations, region, aws_account_id, aws_update_tag,
    )
    load_network_interface_elb_relations(neo4j_session, elb_associations, region, aws_account_id, aws_update_tag)
    load_network_interface_elbv2_relations(neo4j_session, elb_associations_v2, region, aws_account_id, aws_update_tag)
    load_network_interface_instance_to_subnet_relations(neo4j_session, aws_update_tag)
    load_network_interface_load_balancer_relations(neo4j_session, aws_update_tag)


@timeit
def cleanup_network_interfaces(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_ingest_network_interfaces_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_network_interfaces(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.info("Syncing EC2 network interfaces for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_network_interface_data(boto3_session, region)
        load(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_network_interfaces(neo4j_session, common_job_parameters)

import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_subnet_data(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_subnets')
    subnets = []
    for page in paginator.paginate():
        subnets.extend(page['Subnets'])
    return subnets


def load_subnets(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_subnet = """
    MERGE (snet:EC2Subnet{id: {ID}})
    ON CREATE SET snet.firstseen = timestamp()
    SET snet.lastupdated = {aws_update_tag}, snet.name = {NAME}, snet.cidr_block = {CIDR_BLOCK},
    snet.availableipaddresscount = {AVAILABLE_IP_ADDRESS_COUNT}, snet.defaultforaz = {DEFAULT_FOR_AZ},
    snet.mapcustomerownediponlaunch = {MAP_CUSTOMER_OWNED_IP_ON_LAUNCH}, 
    snet.mappubliciponlaunch = {MAP_PUBLIC_IP_ONLAUNCH}, snet.subnetarn = {SUBNET_ARN},
    snet.availabilityzone = {AVAILABILITY_ZONE}, snet.availabilityzoneid = {AVAILABILITY_ZONE_ID},
    snet.subnetid = {SUBNET_ID}
    WITH snet
    MATCH (vpc:AWSVpc{id: {AWS_VPC_ID}})
    MERGE (snet)-[r:VPC_USED]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_subnet_in_aws = """
    MATCH (snet:EC2Subnet{id: {ID}}), (aws:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aws)-[r:RESOURCE]->(snet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for subnet in data:
        subnet_id = subnet["SubnetId"]

        neo4j_session.run(
            ingest_subnet,
            ID=subnet_id,
            NAME=subnet["CidrBlock"],
            SUBNET_ID = subnet['SubnetId'],
            CIDR_BLOCK = subnet["CidrBlock"],
            AVAILABLE_IP_ADDRESS_COUNT = subnet["AvailableIpAddressCount"],
            DEFAULT_FOR_AZ = subnet["DefaultForAz"],
            MAP_CUSTOMER_OWNED_IP_ON_LAUNCH = subnet["MapCustomerOwnedIpOnLaunch"],
            MAP_PUBLIC_IP_ONLAUNCH = subnet["MapPublicIpOnLaunch"],
            SUBNET_ARN = subnet['SubnetArn'],
            AVAILABILITY_ZONE = subnet["AvailabilityZone"],
            AVAILABILITY_ZONE_ID = subnet["AvailabilityZoneId"],
            AWS_VPC_ID = subnet["VpcId"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_subnet_in_aws,
            ID=subnet_id,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        ) 



@timeit
def cleanup_subnets(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_ingest_subnets_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_subnets(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 subnets for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_subnet_data(boto3_session, region)
        load_subnets(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_subnets(neo4j_session, common_job_parameters)

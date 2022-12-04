import time
import logging
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
def get_subnet_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    subnets = []
    try:

        paginator = client.get_paginator('describe_subnets')
        subnets: List[Dict] = []
        for page in paginator.paginate():
            subnets.extend(page['Subnets'])
        for subnet in subnets:
            subnet['region'] = region
            subnet['consolelink'] = aws_console_link.get_console_link(arn=subnet['SubnetArn'])

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                f'ec2:describe_subnets failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise

    return subnets


@timeit
def load_subnets(
    neo4j_session: neo4j.Session, data: List[Dict], aws_account_id: str,
    aws_update_tag: int,
) -> None:

    ingest_subnets = """
    UNWIND $subnets as subnet
    MERGE (snet:EC2Subnet{subnetid: subnet.SubnetId})
    ON CREATE SET snet.firstseen = timestamp()
    SET snet.lastupdated = $aws_update_tag, snet.name = subnet.CidrBlock, snet.cidr_block = subnet.CidrBlock,
    snet.available_ip_address_count = subnet.AvailableIpAddressCount, snet.default_for_az = subnet.DefaultForAz,
    snet.map_customer_owned_ip_on_launch = subnet.MapCustomerOwnedIpOnLaunch,snet.region = subnet.region,
    snet.state = subnet.State, snet.assignipv6addressoncreation = subnet.AssignIpv6AddressOnCreation,
    snet.map_public_ip_on_launch = subnet.MapPublicIpOnLaunch, snet.subnet_arn = subnet.SubnetArn,
    snet.availability_zone = subnet.AvailabilityZone, snet.availability_zone_id = subnet.AvailabilityZoneId,
    snet.subnetid = subnet.SubnetId, snet.arn = subnet.SubnetArn, snet.consolelink = subnet.consolelink
    """

    ingest_subnet_vpc_relations = """
    UNWIND $subnets as subnet
    MATCH (snet:EC2Subnet{subnetid: subnet.SubnetId}), (vpc:AWSVpc{id: subnet.VpcId})
    MERGE (snet)-[r:MEMBER_OF_AWS_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    ingest_subnet_aws_account_relations = """
    UNWIND $subnets as subnet
    MATCH (snet:EC2Subnet{subnetid: subnet.SubnetId}), (aws:AWSAccount{id: $aws_account_id})
    MERGE (aws)-[r:RESOURCE]->(snet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_subnets, subnets=data, aws_update_tag=aws_update_tag,
        aws_account_id=aws_account_id,
    )
    neo4j_session.run(
        ingest_subnet_vpc_relations, subnets=data, aws_update_tag=aws_update_tag,
        aws_account_id=aws_account_id,
    )
    neo4j_session.run(
        ingest_subnet_aws_account_relations, subnets=data, aws_update_tag=aws_update_tag,
        aws_account_id=aws_account_id,
    )


@timeit
def cleanup_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_ingest_subnets_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_subnets(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 subnets for account '%s', at %s.", current_aws_account_id, tic)

    data = []
    for region in regions:
        logger.info("Syncing EC2 subnets for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_subnet_data(boto3_session, region))

    logger.info(f"Total Subnets: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('ec2:subnet', None):
        pageNo = common_job_parameters.get("pagination", {}).get("ec2:subnet", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("ec2:subnet", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for ec2:subnet {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('ec2:subnet', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('ec2:subnet', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('ec2:subnet', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['ec2:subnet']['hasNextPage'] = has_next_page

    load_subnets(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_subnets(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 subnets: {toc - tic:0.4f} seconds")

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
def get_route_tables_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    try:
        paginator = client.get_paginator('describe_route_tables')
        route_tables: List[Dict] = []
        for page in paginator.paginate():
            route_tables.extend(page['RouteTables'])
        for route_table in route_tables:
            route_table['region'] = region
            route_table['consolelink'] = ''  # TODO
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                f'ec2:describe_subnets failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise
    return route_tables


@timeit
def load_route_tables(
    neo4j_session: neo4j.Session, data: List[Dict], aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_route_tables = """
    UNWIND $route_tables as route_table
    MERGE (rtab: EC2RouteTable{id: route_table.RouteTableId})
    ON CREATE SET 
        rtab.firstseen = timestamp()
    SET
        rtab.lastupdated = $aws_update_tag,
        rtab.vpc_id = route_table.VpcId,
        rtab.owner_id = route_table.OwnerId
    WITH rtab, route_table
    UNWIND route_table.Routes as route
    MERGE (rt: EC2Route{id: route.DestinationCidrBlock})
    ON CREATE SET
        rt.firstseen = timestamp()
    SET
        rt.lastupdated = $aws_update_tag,
        rt.destination_cidr_block = route.DestinationCidrBlock,
        rt.destination_ipv6_cidr_block = route.DestinationIpv6CidrBlock,
        rt.gateway_id = route.GatewayId,
        rt.state = route.State,
        rt.nat_gateway_id = route.NatGatewayId
    WITH rtab, route_table, rt
    MERGE (rtab)-[r:MEMBER_OF_ROUTE_TABLE]->(rt)
    ON CREATE SET
        r.firstseen = timestamp()
    SET
        r.lastupdated = $aws_update_tag
    WITH rtab, route_table
    UNWIND route_table.Associations as assoc
    MERGE (asc: EC2RouteTableAssociation{id: assoc.RouteTableAssociationId})
    ON CREATE SET
        asc.firstseen = timestamp()
    SET
        asc.lastupdated = $aws_update_tag,
        asc.subnet_id = assoc.SubnetId,
        asc.main = assoc.Main,
        asc.Gateway_id = assoc.GatewayId
    WITH asc, rtab
    MERGE (rtab)-[rel:HAS_ASSOCIATION]->(asc)
    ON CREATE SET 
        rel.firstseen = timestamp()
    SET
        rel.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        ingest_route_tables,
        route_tables=data,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_route_tables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ec2_route_table_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_route_tables(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 route tables for account '%s', at %s.", current_aws_account_id, tic)

    data = []
    for region in regions:
        logger.info("Syncing EC2 route tables for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_route_tables_data(boto3_session, region))

    logger.info(f"Total route tables: {len(data)}")

    load_route_tables(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_route_tables(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 route tables: {toc - tic:0.4f} seconds")

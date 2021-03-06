import logging
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
def get_internet_gateways(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_internet_gateways()['InternetGateways']


@timeit
def load_internet_gateways(
    neo4j_session: neo4j.Session, data: List[Dict], region: str,
    current_aws_account_id: str, update_tag: int,
) -> None:
    logger.debug("Loading %d Internet Gateways in %s.", len(data), region)
    query = """
            MERGE (ig:AWSInternetGateway{id: {InternetGatewayId}})
            ON CREATE SET
                ig.firstseen = timestamp(),
                ig.region = {Region}
            SET
                ig.ownerid = {OwnerId},
                ig.lastupdated = {aws_update_tag}

            WITH ig
            MATCH (awsAccount:AWSAccount {id: {AWS_ACCOUNT_ID}})
            MERGE (awsAccount)-[r:RESOURCE]->(ig)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {aws_update_tag}

            WITH ig
            MATCH (vpc:AWSVpc{id: {VpcId}})
            MERGE (ig)-[r:ATTACHED_TO]->(vpc)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = {aws_update_tag}

    """

    for gateway in data:
        vpcId = None
        if len(gateway['Attachments']) > 0:
            vpcId = gateway['Attachments'][0]['VpcId']  # IGW can only be attached to one VPC
        neo4j_session.run(
            query,
            InternetGatewayId=gateway['InternetGatewayId'],
            OwnerId=gateway["OwnerId"],
            Region=region,
            VpcId=vpcId,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=update_tag,
        ).consume()


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running Internet Gateway cleanup job.")
    run_cleanup_job('aws_import_internet_gateways_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_internet_gateways(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing Internet Gateways for region '%s' in account '%s'.", region, current_aws_account_id)
        internet_gateways = get_internet_gateways(boto3_session, region)
        load_internet_gateways(neo4j_session, internet_gateways, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

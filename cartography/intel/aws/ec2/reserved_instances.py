import time
import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_reserved_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    reserved_instances = []
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    try:
        reserved_instances = client.describe_reserved_instances()['ReservedInstances']

    except Exception as e:
        logger.warning(f"Failed retrieve reserved instances for region - {region}. Error - {e}")

    return reserved_instances


@timeit
def load_reserved_instances(
        neo4j_session: neo4j.Session, data: List[Dict], region: str,
        current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_reserved_instances = """
    UNWIND $reserved_instances_list as res
    MERGE (ri:EC2ReservedInstance{id: res.ReservedInstancesId})
    ON CREATE SET ri.firstseen = timestamp()
    SET ri.lastupdated = $update_tag, ri.availabilityzone = res.AvailabilityZone, ri.duration = res.Duration,
    ri.end = res.End, ri.start = res.Start, ri.count = res.InstanceCount, ri.type = res.InstanceType,
    ri.productdescription = res.ProductDescription, ri.state = res.State, ri.currencycode = res.CurrencyCode,
    ri.instancetenancy = res.InstanceTenancy, ri.offeringclass = res.OfferingClass,
    ri.offeringtype = res.OfferingType, ri.scope = res.Scope, ri.fixedprice = res.FixedPrice, ri.region=$Region,
    ri.arn = ri.Arn
    WITH ri
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(ri)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # neo4j does not accept datetime objects and values. This loop is used to convert
    # these values to string.
    for r_instance in data:
        r_instance['Start'] = str(r_instance['Start'])
        r_instance['End'] = str(r_instance['End'])
        r_instance['Arn'] = f"arn:aws:ec2:{region}:{current_aws_account_id}:reserved-instances/{r_instance['ReservedInstancesId']}"

    neo4j_session.run(
        ingest_reserved_instances,
        reserved_instances_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def cleanup_reserved_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_reserved_instances_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_reserved_instances(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str,
        update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 Reserved Instances for account '%s', at %s.", current_aws_account_id, tic)

    for region in regions:
        logger.debug("Syncing reserved instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_reserved_instances(boto3_session, region)

        logger.info(f"Total EBS Reserved Instances: {len(data)} for {region}")

        load_reserved_instances(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_reserved_instances(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 Reserved Instances: {toc - tic:0.4f} seconds")

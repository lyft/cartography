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
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    try:
        reserved_instances = client.describe_reserved_instances()['ReservedInstances']
    except ClientError as e:
        logger.warning("Failed retrieve reserved instances for region - {}. Error - {}".format(region, e))
        raise
    return reserved_instances


@timeit
def load_images(
        neo4j_session: neo4j.Session, data: List[Dict], region: str,
        current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_images = """
    UNWIND {images_list} as image
    MERGE (i:EC2Images{id: image.ImageId})
    ON CREATE SET i.firstseen = timestamp(), i.name = image.Name, i.creationdate = image.CreationDate
    SET i.lastupdated = {update_tag},
    i.architecture = image.Architecture, i.location = image.ImageLocation, i.type = image.ImageType,
    i.ispublic = image.Public, i.platform = image.Platform, i.usageoperation = image.UsageOperation,
    i.state = image.State, i.description = image.Description, i.enasupport = image.EnaSupport,
    i.hypervisor = image.Hypervisor, i.rootdevicename = image.RootDeviceName, i.rootdevicetype = image.RootDeviceType,
    i.virtualizationtype = image.VirtualizationType, i.bootmode = image.BootMode, i.region={Region}
    WITH i
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest_images,
        images_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def cleanup_images(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
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
    for region in regions:
        logger.debug("Syncing reserved instances for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_reserved_instances(boto3_session, region)
        load_reserved_instances(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_reserved_instances(neo4j_session, common_job_parameters)

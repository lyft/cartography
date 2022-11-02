import time
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from botocore.exceptions import ClientError
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_volumes(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    volumes = []
    try:
        paginator = client.get_paginator('describe_volumes')
        volumes: List[Dict] = []
        for page in paginator.paginate():
            volumes.extend(page['Volumes'])

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                f'ec2:describe_security_groups failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise

    return volumes


def transform_volumes(volumes: List[Dict[str, Any]], region: str, current_aws_account_id: str) -> List[Dict[str, Any]]:
    for volume in volumes:
        volume['VolumeArn'] = f"arn:aws:ec2:{region}:{current_aws_account_id}:volume/{volume['VolumeId']}"
        volume['CreateTime'] = str(volume['CreateTime'])
        volume['region'] = region
    return volumes


@timeit
def load_volumes(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_volumes = """
    UNWIND $volumes_list as volume
        MERGE (vol:EBSVolume{id: volume.VolumeId})
        ON CREATE SET vol.firstseen = timestamp()
        SET vol.arn = volume.VolumeArn,
            vol.lastupdated = $update_tag,
            vol.availabilityzone = volume.AvailabilityZone,
            vol.createtime = volume.CreateTime,
            vol.encrypted = volume.Encrypted,
            vol.size = volume.Size,
            vol.state = volume.State,
            vol.outpostarn = volume.OutpostArn,
            vol.snapshotid = volume.SnapshotId,
            vol.iops = volume.Iops,
            vol.fastrestored = volume.FastRestored,
            vol.multiattachenabled = volume.MultiAttachEnabled,
            vol.type = volume.VolumeType,
            vol.kmskeyid = volume.KmsKeyId,
            vol.region=volume.region
        WITH vol
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(vol)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_volumes,
        volumes_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


def load_volume_relationships(
        neo4j_session: neo4j.Session,
        volumes: List[Dict[str, Any]],
        aws_update_tag: int,
) -> None:
    add_relationship_query = """
        MATCH (volume:EBSVolume{arn: $VolumeArn})
        WITH volume
        MATCH (instance:EC2Instance{instanceid: $InstanceId})
        MERGE (volume)-[r:ATTACHED_TO_EC2_INSTANCE]->(instance)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    for volume in volumes:
        for attachment in volume.get('Attachments', []):
            if attachment['State'] != 'attached':
                continue
            neo4j_session.run(
                add_relationship_query,
                VolumeArn=volume['VolumeArn'],
                InstanceId=attachment['InstanceId'],
                aws_update_tag=aws_update_tag,
            )


@timeit
def cleanup_volumes(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_volumes_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ebs_volumes(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing volumes for account '%s', at %s.", current_aws_account_id, tic)

    transformed_data = []
    for region in regions:
        logger.debug("Syncing volumes for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_volumes(boto3_session, region)
        transformed_data.extend(transform_volumes(data, region, current_aws_account_id))

    logger.info(f"Total EC2 Volumes: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('ec2:volumes', None):
        pageNo = common_job_parameters.get("pagination", {}).get("ec2:volumes", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("ec2:volumes", None)["pageSize"]
        totalPages = len(transformed_data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for ec2:volumes {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('ec2:volumes', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('ec2:volumes', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('ec2:volumes', {})['pageSize']
        if page_end > len(transformed_data) or page_end == len(transformed_data):
            transformed_data = transformed_data[page_start:]
        else:
            has_next_page = True
            transformed_data = transformed_data[page_start:page_end]
            common_job_parameters['pagination']['ec2:volumes']['hasNextPage'] = has_next_page

    load_volumes(neo4j_session, transformed_data, current_aws_account_id, update_tag)
    load_volume_relationships(neo4j_session, transformed_data, update_tag)
    cleanup_volumes(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Volumes: {toc - tic:0.4f} seconds")

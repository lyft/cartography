import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_volumes(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    paginator = client.get_paginator('describe_volumes')
    volumes: List[Dict] = []
    for page in paginator.paginate():
        volumes.extend(page['Volumes'])
    return volumes


@timeit
def load_volumes(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_volumes = """
    UNWIND {volumes_list} as volume
        MERGE (v:EBSVolume{id: volume.VolumeId})
        ON CREATE SET v.firstseen = timestamp()
        SET v.lastupdated = {update_tag}, v.availabilityzone = volume.AvailabilityZone,
        v.createtime = volume.CreateTime, v.encrypted = volume.Encrypted, v.size = volume.Size, v.state = volume.State,
        v.outpostarn = volume.OutpostArn, v.snapshotid = volume.SnapshotId, v.iops = volume.Iops, 
        v.type = volume.VolumeType, v.kmskeyid = volume.KmsKeyId, v.region={Region}
        v.fastrestored = volume.FastRestored, v.multiattachenabled = volume.MultiAttachEnabled,
        WITH v
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {update_tag}
    """

    for volume in data:
        volume['CreateTime'] = str(volume['CreateTime'])

    neo4j_session.run(
        ingest_volumes,
        volumes_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
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
    for region in regions:
        logger.debug("Syncing volumes for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_volumes(boto3_session, region)
        load_volumes(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_volumes(neo4j_session, common_job_parameters)

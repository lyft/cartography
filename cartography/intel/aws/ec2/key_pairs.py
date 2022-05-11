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
def get_ec2_key_pairs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    key_pairs = client.describe_key_pairs()['KeyPairs']
    for keykey_pair in key_pairs:
        keykey_pair['region'] = region
    return key_pairs


@timeit
def load_ec2_key_pairs(
    neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: {ARN}, id: {ARN}})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = {KeyName}, keypair.keyfingerprint = {KeyFingerprint}, keypair.region = {Region},
    keypair.lastupdated = {update_tag}
    WITH keypair
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    for key_pair in data:
        region = key_pair.get('region', '')
        key_name = key_pair["KeyName"]
        key_fingerprint = key_pair.get("KeyFingerprint")
        key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'

        neo4j_session.run(
            ingest_key_pair,
            ARN=key_pair_arn,
            KeyName=key_name,
            KeyFingerprint=key_fingerprint,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            update_tag=update_tag,
        )


@timeit
def cleanup_ec2_key_pairs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ec2_key_pairs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_ec2_key_pairs(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        logger.info("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data.append(get_ec2_key_pairs(boto3_session, region))

    if common_job_parameters.get('pagination', {}).get('ec2:keypair', None):
        has_next_page = False
        page_start = (common_job_parameters['pageNo'] - 1) * common_job_parameters['pageSize']
        page_end = page_start + common_job_parameters['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
        common_job_parameters['pagination']['ec2:keypair']['hasNextPage'] = has_next_page

    load_ec2_key_pairs(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)

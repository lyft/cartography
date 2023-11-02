import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.keypairs import EC2KeyPairSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker
from botocore.exceptions import ClientError
logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_ec2_key_pairs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    keys = []
    try:
        keys = client.describe_key_pairs().get('KeyPairs', [])
        for keykey_pair in keys:
            keykey_pair['region'] = region
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                f'ec2:describe_key_pairs failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise

    return keys

@timeit
def load_ec2_key_pairs(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: $ARN, id: $ARN})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = $KeyName, keypair.keyfingerprint = $KeyFingerprint, keypair.region = $Region,
    keypair.lastupdated = $update_tag,keypair.consolelink=$consolelink
    WITH keypair
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    for key_pair in data:
        key_name = key_pair["KeyName"]
        key_fingerprint = key_pair.get("KeyFingerprint")
        key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'
        consolelink = ''
        try:
            consolelink = aws_console_link.get_console_link(arn=key_pair_arn)
        except Exception as e:
            print(e)
        neo4j_session.run(
            ingest_key_pair,
            ARN=key_pair_arn,
            KeyName=key_name,
            KeyFingerprint=key_fingerprint,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            consolelink=consolelink,
            update_tag=update_tag,
        )


@timeit
def cleanup_ec2_key_pairs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(EC2KeyPairSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_ec2_key_pairs(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 key pairs for account '%s', at %s.", current_aws_account_id, tic)

    for region in regions:
        logger.info("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_key_pairs(boto3_session, region)
        load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process EC2 key pairs: {toc - tic:0.4f} seconds")

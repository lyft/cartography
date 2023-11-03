import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
import time
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.images import EC2ImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker
aws_console_link = AWSLinker()
logger = logging.getLogger(__name__)


@timeit
def get_images_in_use(neo4j_session: neo4j.Session, region: str, current_aws_account_id: str) -> List[str]:
    # We use OPTIONAL here to allow query chaining with queries that may not match.
    get_images_query = """
    OPTIONAL MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(i:EC2Instance)
    WHERE i.region = $Region
    WITH collect(DISTINCT i.imageid) AS images
    OPTIONAL MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(lc:LaunchConfiguration)
    WHERE lc.region = $Region
    WITH collect(DISTINCT lc.image_id)+images AS images
    OPTIONAL MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(ltv:LaunchTemplateVersion)
    WHERE ltv.region = $Region
    WITH collect(DISTINCT ltv.image_id)+images AS images
    RETURN images
    """
    results = neo4j_session.run(get_images_query, AWS_ACCOUNT_ID=current_aws_account_id, Region=region)
    images = []
    for r in results:
        images.extend(r['images'])
    return images

@timeit
@aws_handle_regions
def get_images(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config(),)
    images = []
    try:
        self_images = client.describe_images(Owners=['self'])['Images']
        images.extend(self_images)
    except ClientError as e:
        logger.warning(f"Failed retrieve images for region - {region}. Error - {e}")
    return images

@timeit
def transform_images(boto3_session: boto3.session.Session, imags: List[Dict], image_ids: List[str], region: str, account_id: str) -> List[Dict]:
    images = []
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config(),)
    try:
        if image_ids:
            images_in_use = client.describe_images(ImageIds=image_ids)['Images']
            # Ensure we're not adding duplicates
            _ids = [image["ImageId"] for image in imags]
            for image in images_in_use:
                if image["ImageId"] not in _ids:
                    console_arn = f"arn:aws:ec2:{region}:{account_id}:image/{image['ImageId']}"
                    image['consolelink'] = aws_console_link.get_console_link(arn=console_arn)
                    image['region'] = region
                    images.append(image)
    except ClientError as e:
        logger.warning(f"Failed retrieve images for region - {region}. Error - {e}")
    return images

@timeit
@aws_handle_regions
def get_images(boto3_session: boto3.session.Session, region: str, image_ids: List[str]) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    images = []
    try:
        self_images = client.describe_images(Owners=['self'])['Images']
        images.extend(self_images)
    except ClientError as e:
        logger.warning(f"Failed retrieve images for region - {region}. Error - {e}")
    try:
        if image_ids:
            images_in_use = client.describe_images(ImageIds=image_ids)['Images']
            # Ensure we're not adding duplicates
            _ids = [image["ImageId"] for image in images]
            for image in images_in_use:
                if image["ImageId"] not in _ids:
                    images.append(image)
    except ClientError as e:
        logger.warning(f"Failed retrieve images for region - {region}. Error - {e}")
    return images


@timeit
def load_images(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str, update_tag: int,
) -> None:
    # AMI IDs are unique to each AWS Region. Hence we make an 'ID' string that is a combo of ImageId and region
    for image in data:
        image['ID'] = image['ImageId'] + '|' + image.get('region', '')
        image['arn'] = f"arn:aws:ec2:{image.get('region', '')}:{current_aws_account_id}:image/{image['ImageId']}"

    load(
        neo4j_session,
        EC2ImageSchema(),
        data,
        lastupdated=update_tag,
        Region=image.get('region', ''),
        AWS_ID=current_aws_account_id,
    )
@timeit
def cleanup_images(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    cleanup_job = GraphJob.from_node_schema(EC2ImageSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_ec2_images(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing images for account '%s', at %s.", current_aws_account_id, tic)
    data = []
    for region in regions:
        logger.info("Syncing images for region '%s' in account '%s'.", region, current_aws_account_id)
        images_in_use = get_images_in_use(neo4j_session, region, current_aws_account_id)
        imgs = get_images(boto3_session, region)
        data = transform_images(boto3_session, imgs, images_in_use, region, current_aws_account_id)
    logger.info(f"Total EC2 Images: {len(data)}")
    load_images(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_images(neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process Images: {toc - tic:0.4f} seconds")

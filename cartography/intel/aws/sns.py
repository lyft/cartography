import time
import logging
from typing import Dict
from typing import List
from botocore.exceptions import ClientError

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_sns_topic(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    topics = []
    try:
        client = boto3_session.client('sns', region_name=region)
        paginator = client.get_paginator('list_topics')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            topics.extend(page.get('Topics', []))
        for topic in topics:
            topic['region'] = region
            topic['name'] = topic['TopicArn'].split(':')[-1]

        return topics

    except ClientError as e:
        logger.error(f'Failed to call SNS list_topics: {region} - {e}')
        return topics


def load_sns_topic(session: neo4j.Session, topics: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_sns_topic_tx, topics, current_aws_account_id, aws_update_tag)


@timeit
def _load_sns_topic_tx(tx: neo4j.Transaction, topics: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (topic:AWSSNSTopic{id: record.TopicArn})
    ON CREATE SET topic.firstseen = timestamp(),
        topic.arn = record.TopicArn
    SET topic.lastupdated = {aws_update_tag},
        topic.name = record.name,
        topic.region = record.region
    WITH topic
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(topic)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=topics,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_sns_topic(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_sns_topic_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing SNS for account '%s', at %s.", current_aws_account_id, tic)

    topics = []
    for region in regions:
        logger.info("Syncing SNS for region '%s' in account '%s'.", region, current_aws_account_id)

        topics.extend(get_sns_topic(boto3_session, region))

    if common_job_parameters.get('pagination', {}).get('sns', None):
        pageNo = common_job_parameters.get("pagination", {}).get("sns", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("sns", None)["pageSize"]
        totalPages = len(topics) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for SNS topics {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('sns', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('sns', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('sns', {})['pageSize']
        if page_end > len(topics) or page_end == len(topics):
            topics = topics[page_start:]

        else:
            has_next_page = True
            topics = topics[page_start:page_end]
            common_job_parameters['pagination']['sns']['hasNextPage'] = has_next_page

    load_sns_topic(neo4j_session, topics, current_aws_account_id, update_tag)

    cleanup_sns_topic(neo4j_session, common_job_parameters)

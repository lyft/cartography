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
from cloudconsolelink.clouds.aws import AWSLinker

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()

@aws_handle_regions
@timeit
def list_subscriptions(boto3_session: boto3.session.Session, region):
    # List all Subscriptions
    subscriptions = []
    try:
        client = boto3_session.client('sns', region_name=region)
        paginator = client.get_paginator('list_subscriptions')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            subscriptions.extend(page.get('Subscriptions', []))

    except ClientError as e:
        logger.error(f'Failed to call SNS list_subscriptions: {region} - {e}')

    for subscription in subscriptions:
        # subscription arn - arn:aws:sns:<region>:<account_id>:<topic_name>:<subscription_id>
        subscription['arn'] = subscription['SubscriptionArn']
        subscription['consolelink'] = aws_console_link.get_console_link(arn=subscription['arn'])
        subscription['region'] = region
        subscription['name'] = subscription['SubscriptionArn'].split(':')[-1]

    return subscriptions


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

        subscriptions = list_subscriptions(boto3_session, region)

        for topic in topics:
            topic['region'] = region
            topic['name'] = topic['TopicArn'].split(':')[-1]
            topic['consolelink'] = aws_console_link.get_console_link(arn=topic['arn'])
            topic['attributes'] = client.get_topic_attributes(TopicArn=topic['TopicArn']).get('Attributes', {})
            topic['subscriptions'] = list(filter(lambda s: s['TopicArn'] == topic['TopicArn'], subscriptions))

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
        topic.consolelink = record.consolelink,
        topic.region = record.region,
        topic.subscriptions_confirmed = record.attributes.SubscriptionsConfirmed,
        topic.display_name = record.attributes.DisplayName,
        topic.subscriptions_deleted = record.attributes.SubscriptionsDeleted,
        topic.owner = record.attributes.Owner,
        topic.subscriptions_pending = record.attributes.SubscriptionsPending,
        topic.kms_master_key_id = record.attributes.KmsMasterKeyId
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
def load_sns_subscription_topic(session: neo4j.Session, subscriptions: List[Dict], topic_arn: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_sns_topic_subscription_tx, subscriptions, topic_arn, aws_update_tag)


@timeit
def _load_sns_topic_subscription_tx(tx: neo4j.Transaction, subscriptions: List[Dict], topic_arn: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (sub:AWSSNSTopicSubscription{id: record.SubscriptionArn})
    ON CREATE SET sub.firstseen = timestamp(),
        sub.arn = record.SubscriptionArn
    SET sub.lastupdated = {aws_update_tag},
        sub.name = record.name,
        sub.region = record.region,
        sub.consolelink = record.consolelink,
        sub.Endpoint = record.Endpoint,
        sub.Protocol = record.Protocol,
        sub.owner = record.Owner
    WITH sub
    MATCH (owner:AWSSNSTopic{id: {Topic_ARN}})
    MERGE (owner)-[r:RESOURCE]->(sub)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=subscriptions,
        Topic_ARN=topic_arn,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_sns_topic_subscription(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_sns_topic_subscription_cleanup.json', neo4j_session, common_job_parameters)


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

    logger.info(f"Total SNS Topics: {len(topics)}")

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

    for topic in topics:
        load_sns_subscription_topic(neo4j_session, topic['subscriptions'], topic['TopicArn'], update_tag)

    cleanup_sns_topic_subscription(neo4j_session, common_job_parameters)
    cleanup_sns_topic(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process SNS: {toc - tic:0.4f} seconds")

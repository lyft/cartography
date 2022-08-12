import json
import logging
from typing import Dict
from typing import List

import time
import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from . import label
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_pubsub_subscriptions(pubsub: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    subscriptions = []
    try:
        req = pubsub.projects().subscriptions().list(project=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('subscriptions'):
                for subscription in res['subscriptions']:
                    subscription['project_id'] = project_id
                    subscription['region'] = 'global'
                    subscription['id'] = subscription['name']
                    subscription['subscription_name'] = subscription.get('name').split('/')[-1]
                    subscriptions.append(subscription)
            req = pubsub.projects().subscriptions().list_next(previous_request=req, previous_response=res)

        return subscriptions
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve pubsub subscriptions on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_pubsub_subscriptions(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_pubsub_subscriptions_tx, data_list, project_id, update_tag)


@timeit
def load_pubsub_subscriptions_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND {Records} as record
    MERGE (subscription:GCPPubsubSubscription{id:record.id})
    ON CREATE SET
        subscription.firstseen = timestamp()
    SET
        subscription.lastupdated = {gcp_update_tag},
        subscription.region = record.region,
        subscription.name = record.subscription_name,
        subscription.topic = record.topic,
        subscription.ack_deadline_seconds = record.ackDeadlineSeconds,
        subscription.retain_acked_messages = record.retainAckedMessages,
        subscription.enable_message_ordering = record.enableMessageOrdering,
        subscription.filter = record.filter,
        subscription.topic_message_retention_duration = record.topicMessageRetentionDuration,
        subscription.enable_exactly_once_delivery = record.enableExactlyOnceDelivery,
        subscription.detached = record.detached,
        subscription.state = record.state,
        subscription.message_retention_duration = record.messageRetentionDuration
    WITH subscription, record
    MATCH (topic:GCPPubsubTopic{id:record.topic})
    MERGE (topic)-[rt:HAS]->(subscription)
    ON CREATE SET
        rt.firstseen = timestamp()
    SET rt.lastupdated = {gcp_update_tag}
    WITH subscription
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(subscription)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_pubsub_subscriptions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_pubsub_subscriptions_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_pubsub_topics(pubsub: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    topics = []
    try:
        req = pubsub.projects().topics().list(project=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('topics'):
                for topic in res['topics']:
                    topic['project_id'] = project_id
                    topic['region'] = 'global'
                    topic['id'] = topic['name']
                    topic['topic_name'] = topic.get('name').split('/')[-1]
                    topics.append(topic)
            req = pubsub.projects().topics().list_next(previous_request=req, previous_response=res)

        if common_job_parameters.get('pagination', {}).get('pubsub', None):
            pageNo = common_job_parameters.get("pagination", {}).get("pubsub", None)["pageNo"]
            pageSize = common_job_parameters.get("pagination", {}).get("pubsub", None)["pageSize"]
            totalPages = len(topics) / pageSize
            if int(totalPages) != totalPages:
                totalPages = totalPages + 1
            totalPages = int(totalPages)
            if pageNo < totalPages or pageNo == totalPages:
                logger.info(f'pages process for pubsub topics {pageNo}/{totalPages} pageSize is {pageSize}')
            page_start = (common_job_parameters.get('pagination', {}).get('pubsub', None)[
                          'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('pubsub', None)['pageSize']
            page_end = page_start + common_job_parameters.get('pagination', {}).get('pubsub', None)['pageSize']
            if page_end > len(topics) or page_end == len(topics):
                topics = topics[page_start:]
            else:
                has_next_page = True
                topics = topics[page_start:page_end]
                common_job_parameters['pagination']['pubsub']['hasNextPage'] = has_next_page

        return topics
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve pubsub topics on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_pubsub_topics(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_pubsub_topics_tx, data_list, project_id, update_tag)


@timeit
def load_pubsub_topics_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND {Records} as record
    MERGE (topic:GCPPubsubTopic{id:record.id})
    ON CREATE SET
        topic.firstseen = timestamp()
    SET
        topic.lastupdated = {gcp_update_tag},
        topic.region = record.region,
        topic.name = record.topic_name,
        topic.kms_key_name = record.kmsKeyName,
        topic.satisfies_pzs = record.satisfiesPzs,
        topic.message_retention_duration = record.messageRetentionDuration
    WITH topic
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(topic)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_pubsub_topics(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_pubsub_topics_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, pubsub: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:

    tic = time.perf_counter()
    logger.info("Syncing Pubsub for project '%s', at %s.", project_id, tic)

    topics = get_pubsub_topics(pubsub, project_id, regions, common_job_parameters)
    load_pubsub_topics(neo4j_session, topics, project_id, gcp_update_tag)

    label.sync_labels(neo4j_session, topics, gcp_update_tag,
                      common_job_parameters, 'pubsub_topics', 'GCPPubsubTopic')

    if common_job_parameters.get('pagination', {}).get('pubsub', None):
        if not common_job_parameters.get('pagination', {}).get('pubsub', {}).get('hasNextPage', False):
            subscriptions = get_pubsub_subscriptions(pubsub, project_id, regions, common_job_parameters)
            load_pubsub_subscriptions(neo4j_session, subscriptions, project_id, gcp_update_tag)

            cleanup_pubsub_subscriptions(neo4j_session, common_job_parameters)
            label.sync_labels(neo4j_session, subscriptions, gcp_update_tag,
                              common_job_parameters, 'pubsub_subscription', 'GCPPubsubSubscription')

    else:
        subscriptions = get_pubsub_subscriptions(pubsub, project_id, regions, common_job_parameters)
        load_pubsub_subscriptions(neo4j_session, subscriptions, project_id, gcp_update_tag)

        cleanup_pubsub_subscriptions(neo4j_session, common_job_parameters)
        label.sync_labels(neo4j_session, subscriptions, gcp_update_tag,
                          common_job_parameters, 'pubsub_subscription', 'GCPPubsubSubscription')

    cleanup_pubsub_topics(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Pubsub: {toc - tic:0.4f} seconds")

import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource
from cloudconsolelink.clouds.gcp import GCPLinker

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_pubsublite_topics(pubsublite: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    topics = []
    try:
        req = pubsublite.admin().projects().locations().topics().list(parent=f"projects/{project_id}/locations/*")
        while req is not None:
            res = req.execute()
            if res.get('topics'):
                topics.extend(res.get('topics', []))
            req = pubsublite.admin().projects().locations().topics().list_next(previous_request=req, previous_response=res)
        return topics
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve pubsublite topics on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_pubsublite_topics(topics: List[Dict], project_id: str) -> List[Dict]:
    list_topics = []
    for topic in topics:
        topic['project_id'] = project_id,
        topic['region'] = 'global'
        topic['topic_name'] = topic['name'].split('/')[-1]
        topic['consolelink'] = ''  # TODO
        list_topics.append(topic)
    return list_topics


@timeit
def load_pubsublite_topics(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_pubsublite_topics_tx, data_list, project_id, update_tag)


@timeit
def load_pubsublite_topics_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (topic:GCPPubSubLiteTopic{name: record.name})
    ON CREATE SET
        topic.firstseen = timestamp()
    SET
        topic.lastupdated = $gcp_update_tag,
        topic.region = record.region,
        topic.name = record.name,
        topic.consolelink = record.consolelink,
        topic.publish_mib_per_sec = record.partitionConfig.capacity.publishMibPerSec,
        topic.subscribe_mib_per_sec = record.partitionConfig.capacity.subscribeMibPerSec,
        topic.count = record.partitionConfig.count,
        topic.scale = record.partitionConfig.scale,
        topic.throughput_reservation = record.reservationConfig.throughputReservation,
        topic.per_partition_bytes = record.retentionConfig.perPartitionBytes,
        topic.period = record.retentionConfig.period
    WITH topic
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(topic)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def get_pubsublite_subscriptions(pubsublite: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    subscriptions = []
    try:
        req = pubsublite.admin().projects().locations().subscriptions().list(parent=f"projects/{project_id}/locations/*")
        while req is not None:
            res = req.execute()
            if res.get('topics'):
                subscriptions.extend(res.get('topics', []))
            req = pubsublite.admin().projects().locations().subscriptions().list_next(previous_request=req, previous_response=res)
        return subscriptions
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve pubsublite subscriptions on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_pubsublite_subscriptions(subscriptions: List[Dict], project_id: str) -> List[Dict]:
    list_subscriptions = []
    for subscription in subscriptions:
        subscription['project_id'] = project_id,
        subscription['region'] = 'global'
        subscription['subscription_name'] = subscription['name'].split('/')[-1]
        subscription['consolelink'] = ''  # TODO
        list_subscriptions.append(subscription)
    return list_subscriptions


@timeit
def load_pubsublite_subscriptions(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_pubsublite_subscriptions_tx, data_list, project_id, update_tag)


@timeit
def load_pubsublite_subscriptions_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (subscription:GCPPubSubLiteSubscription{name: record.name})
    ON CREATE SET
        subscription.firstseen = timestamp()
    SET
        subscription.lastupdated = $gcp_update_tag,
        subscription.region = record.region,
        subscription.name = record.name,
        subscription.consolelink = record.consolelink,
        subscription.delivery_requirement = record.deliveryConfig.deliveryRequirement,
        subscription.current_state = record.exportConfig.currentState,
        subscription.dead_letter_topic = record.exportConfig.deadLetterTopic,
        subscription.desired_state = record.exportConfig.desiredState,
        subscription.config_topic = record.exportConfig.pubsubConfig.topic,
        subscription.topic = record.topic
    WITH subscription, record
    MATCH (topic:GCPPubSubLiteTopic{name: record.topic})
    MERGE (topic)-[r:HAS]->(subscription)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH subscription
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(subscription)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, pubsub: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing Pubsublite for project '%s', at %s.", project_id, tic)

    topics = get_pubsublite_topics()

    toc = time.perf_counter()
    logger.info(f"Time to process Pubsublite: {toc - tic:0.4f} seconds")

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
def get_dataflow_jobs(dataflow: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    jobs = []
    try:
        req = dataflow.projects().jobs().list(projectId=project_id)
        while req is not None:
            res = req.execute()
            if res.get('jobs'):
                jobs.extend(res.get('jobs', []))
            req = dataflow.projects().jobs().list_next(previous_request=req, previous_response=res)
        return jobs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve dataflow jobs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_jobs(jobs: List[Dict], project_id: str) -> List[Dict]:
    transformed_jobs = []
    for job in jobs:
        job['consolelink'] = ''  # gcp_console_link.get_console_link(project_id=project_id, topic_id=topic['topic_name'], resource_name='cloud_pubsub_topic')
        transformed_jobs.append(job)
    return transformed_jobs


@timeit
def load_dataflow_jobs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_dataflow_jobs_tx, data_list, project_id, update_tag)


@timeit
def load_dataflow_jobs_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (job:GCPDataFlowJob{id:record.id})
    ON CREATE SET
        job.firstseen = timestamp()
    SET
        job.lastupdated = $gcp_update_tag,
        job.region = record.location,
        job.id = record.id,
        job.name = record.name,
        job.replace_job_id = record.replaceJobId,
        job.type = record.type,
        job.cluster_manager_api_service = record.environment.clusterManagerApiService,
        job.dataset = record.environment.dataset,
        job.service_account_email = record.environment.serviceAccountEmail,
        job.service_kms_key_name = record.environment.serviceKmsKeyName,
        job.shuffle_mode = record.en
        job.current_state = record.currentState,
        job.requested_state = record.requestedState,
        job.consolelink = record.consolelink,
        
        topic.satisfies_pzs = record.satisfiesPzs,
    WITH topic
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(topic)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
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

    tops = get_pubsub_topics(pubsub, project_id, regions, common_job_parameters)
    topics = transform_topics(tops, project_id)
    load_pubsub_topics(neo4j_session, topics, project_id, gcp_update_tag)

    label.sync_labels(
        neo4j_session, topics, gcp_update_tag,
        common_job_parameters, 'pubsub_topics', 'GCPPubsubTopic',
    )

    if common_job_parameters.get('pagination', {}).get('pubsub', None):
        if not common_job_parameters.get('pagination', {}).get('pubsub', {}).get('hasNextPage', False):
            subs = get_pubsub_subscriptions(pubsub, project_id, regions, common_job_parameters)
            subscriptions = transform_subscriptions(subs, project_id)
            load_pubsub_subscriptions(neo4j_session, subscriptions, project_id, gcp_update_tag)

            cleanup_pubsub_subscriptions(neo4j_session, common_job_parameters)
            label.sync_labels(
                neo4j_session, subscriptions, gcp_update_tag,
                common_job_parameters, 'pubsub_subscription', 'GCPPubsubSubscription',
            )

    else:
        subs = get_pubsub_subscriptions(pubsub, project_id, regions, common_job_parameters)
        subscriptions = transform_subscriptions(subs, project_id)
        load_pubsub_subscriptions(neo4j_session, subscriptions, project_id, gcp_update_tag)

        cleanup_pubsub_subscriptions(neo4j_session, common_job_parameters)
        label.sync_labels(
            neo4j_session, subscriptions, gcp_update_tag,
            common_job_parameters, 'pubsub_subscription', 'GCPPubsubSubscription',
        )

    cleanup_pubsub_topics(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Pubsub: {toc - tic:0.4f} seconds")

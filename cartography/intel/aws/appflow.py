import json
import logging
from typing import Dict
from typing import List
from pprint import pprint

import boto3
import neo4j

from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
# @aws_handle_regions  # ask about this tag
def get_appflows(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3.client('appflow')


    flows = client.list_flows()

    print("flows are ---------------")
    pprint(flows)

    paginator = client.get_paginator("list_flows")

    flows = []

    for page in paginator.paginate():
        for flow in page['flows']:
            flows.append(flow)

    return flows


@timeit
def load_appflows(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        data: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_distribution = """
             MERGE (d:AppFlow{id: $distribution.flowArn})
             ON CREATE SET d.firstseen = timestamp()
             SET d.arn = $distribution.flowArn,
                 d.name = $distribution.flowName,
                 d.status = $distribution.flowStatus,
                 d.description = $distribution.description,
                 d.created_at = $distribution.createdAt,
                 d.sourceConnectorType = $distribution.sourceConnectorType,
                 d.sourceConnectorLabel = $distribution.sourceConnectorLabel,
                 d.destinationConnectorType = $distribution.destinationConnectorType,
                 d.destinationConnectorLabel = $distribution.destinationConnectorLabel,
                 d.triggerType = $distribution.triggerType,
                 d.createdBy = $distribution.createdBy,
                 d.lastUpdatedBy = $distribution.lastUpdatedBy,
                 d.tags = $distribution.tags,
                 d.lastRunExecutionDetails = $distribution.lastRunExecutionDetails,
                 d.lastupdated = $aws_update_tag
             WITH d
             MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
             MERGE (owner)-[r:RESOURCE]->(d)
             ON CREATE SET r.firstseen = timestamp()
             SET r.lastupdated = $aws_update_tag
         """

    for flow in data:
        flow["createdAt"] = dict_date_to_epoch(flow, 'createdAt')

        # ask if we want to add this in the distribution since we already have lastupdated
        flow["lastUpdatedAt"] = dict_date_to_epoch(flow, 'lastUpdatedAt')

        flow["tags"] = json.dumps(flow["tags"])
        flow["lastRunExecutionDetails"] = json.dumps(flow["lastRunExecutionDetails"])

        neo4j_session.run(
            ingest_distribution,
            distribution=flow,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def sync_appflow(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    flows_data = get_appflows(boto3_session)
    load_appflows(neo4j_session, boto3_session, flows_data, current_aws_account_id,
                                       aws_update_tag)


@timeit
def cleanup_appflow(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    # to do
    print("cleaning up")
    # run_cleanup_job('aws_import_elasticbeanstalk_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict,
) -> None:
    logger.info(f"Syncing AppFlow in account '{current_aws_account_id}'.")
    sync_appflow(neo4j_session, boto3_session, current_aws_account_id, update_tag)
    cleanup_appflow(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='CloudFrontDistribution',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

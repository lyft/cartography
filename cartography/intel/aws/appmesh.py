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
def get_appmesh(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3.client('appmesh')

    paginator = client.get_paginator("list_meshes")

    meshs = []

    for page in paginator.paginate():
        for mesh in page['meshes']:
            meshs.append(mesh)

    return meshs


@timeit
def load_appmesh(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        data: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_distribution = """
             MERGE (d:AppMesh{id: $distribution.arn})
             ON CREATE SET d.firstseen = timestamp()
             SET d.arn = $distribution.arn,
                 d.name = $distribution.meshName,
                 d.owner = $distribution.meshOwner,
                 d.resource_owner = $distribution.resourceOwner,
                 d.version = $distribution.version,
                 d.created_at = $distribution.createdAt,
                 d.lastupdated = $aws_update_tag
             WITH d
             MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
             MERGE (owner)-[r:RESOURCE]->(d)
             ON CREATE SET r.firstseen = timestamp()
             SET r.lastupdated = $aws_update_tag
         """

    for mesh in data:
        mesh["createdAt"] = dict_date_to_epoch(mesh, 'createdAt')

        # ask if we want to add this in the distribution since we already have lastupdated
        mesh["lastUpdatedAt"] = dict_date_to_epoch(mesh, 'lastUpdatedAt')

        neo4j_session.run(
            ingest_distribution,
            distribution=mesh,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def sync_appmesh(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    mesh_data = get_appmesh(boto3_session)
    load_appmesh(neo4j_session, boto3_session, mesh_data, current_aws_account_id,
                 aws_update_tag)


@timeit
def cleanup_appmesh(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
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
    sync_appmesh(neo4j_session, boto3_session, current_aws_account_id, update_tag)
    cleanup_appmesh(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='CloudFrontDistribution',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

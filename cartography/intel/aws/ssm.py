import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_instance_ids(neo4j_session: neo4j.Session, region: str, current_aws_account_id: str) -> List[str]:
    get_instances_query = """
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(i:EC2Instance)
    WHERE i.region = $Region
    RETURN i.id
    """
    results = neo4j_session.run(get_instances_query, AWS_ACCOUNT_ID=current_aws_account_id, Region=region)
    instance_ids = []
    for r in results:
        instance_ids.append(r['i.id'])
    return instance_ids


@timeit
@aws_handle_regions
def get_instance_information(
    boto3_session: boto3.session.Session, region: str, instance_ids: List[str],
) -> List[Dict[str, Any]]:
    client = boto3_session.client('ssm', region_name=region)
    instance_information: List[Dict[str, Any]] = []
    paginator = client.get_paginator('describe_instance_information')
    for i in range(0, len(instance_ids), 50):
        instance_ids_chunk = instance_ids[i:i + 50]
        for info_chunk in paginator.paginate(
            Filters=[{"Key": "InstanceIds", "Values": instance_ids_chunk}],
            MaxResults=50,
        ):
            instance_information.extend(info_chunk.get('InstanceInformationList', []))
    return instance_information


@timeit
@aws_handle_regions
def get_instance_patches(
    boto3_session: boto3.session.Session, region: str, instance_ids: List[str],
) -> List[Dict[str, Any]]:
    client = boto3_session.client('ssm', region_name=region)
    instance_patches: List[Dict[str, Any]] = []
    paginator = client.get_paginator('describe_instance_patches')
    for instance_id in instance_ids:
        patches = []
        for page in paginator.paginate(InstanceId=instance_id):
            patches.extend(page["Patches"])
        # to avoid complicating the load function, inject the instance ID into the patch
        for patch in patches:
            patch["_instance_id"] = instance_id
        instance_patches.extend(patches)
    return instance_patches


@timeit
def load_instance_information(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $InstanceInformation AS instance
        MERGE (i:SSMInstanceInformation{id: instance.InstanceId})
        ON CREATE SET i.firstseen = timestamp()
        SET i.instance_id = instance.InstanceId,
            i.ping_status = instance.PingStatus,
            i.last_ping_date_time = instance.LastPingDateTime,
            i.agent_version = instance.AgentVersion,
            i.is_latest_version = instance.IsLatestVersion,
            i.platform_type = instance.PlatformType,
            i.platform_name = instance.PlatformName,
            i.platform_version = instance.PlatformVersion,
            i.activation_id = instance.ActivationId,
            i.iam_role = instance.IamRole,
            i.registration_date = instance.RegistrationDate,
            i.resource_type = instance.ResourceType,
            i.name = instance.Name,
            i.ip_address = instance.IPAddress,
            i.computer_name = instance.ComputerName,
            i.association_status = instance.AssociationStatus,
            i.last_association_execution_date = instance.LastAssociationExecutionDate,
            i.last_successful_association_execution_date = instance.LastSuccessfulAssociationExecutionDate,
            i.source_id = instance.SourceId,
            i.source_type = instance.SourceType,
            i.region = $Region,
            i.lastupdated = $aws_update_tag
        WITH i
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(i)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH i
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(ec2_instance:EC2Instance{id: i.instance_id})
        MERGE (ec2_instance)-[r2:HAS_INFORMATION]->(i)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
    """
    for ii in data:
        ii["LastPingDateTime"] = dict_date_to_epoch(ii, "LastPingDateTime")
        ii["RegistrationDate"] = dict_date_to_epoch(ii, "RegistrationDate")
        ii["LastAssociationExecutionDate"] = dict_date_to_epoch(ii, "LastAssociationExecutionDate")
        ii["LastSuccessfulAssociationExecutionDate"] = dict_date_to_epoch(ii, "LastSuccessfulAssociationExecutionDate")

    neo4j_session.run(
        ingest_query,
        InstanceInformation=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_instance_patches(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_query = """
    UNWIND $InstancePatch AS patch
        MERGE (p:SSMInstancePatch{id: patch._instance_id + "-" + patch.Title})
        ON CREATE SET p.firstseen = timestamp()
        SET p.instance_id = patch._instance_id,
            p.title = patch.Title,
            p.kb_id = patch.KBId,
            p.classification = patch.Classification,
            p.severity = patch.Severity,
            p.state = patch.State,
            p.installed_time = patch.InstalledTime,
            p.cve_ids = patch.CVEIds,
            p.region = $Region,
            p.lastupdated = $aws_update_tag
        WITH p
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(p)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH p
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(ec2_instance:EC2Instance{id: p.instance_id})
        MERGE (ec2_instance)-[r2:HAS_PATCH]->(p)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
    """
    for p in data:
        p["InstalledTime"] = dict_date_to_epoch(p, "InstalledTime")
        # Split the comma separated CVEIds, if they exist, and strip
        # the empty string from the list if not.
        p["CVEIds"] = list(filter(None, p.get("CVEIds", "").split(",")))

    neo4j_session.run(
        ingest_query,
        InstancePatch=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_ssm(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ssm_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing SSM for region '%s' in account '%s'.", region, current_aws_account_id)
        instance_ids = get_instance_ids(neo4j_session, region, current_aws_account_id)
        data = get_instance_information(boto3_session, region, instance_ids)
        load_instance_information(neo4j_session, data, region, current_aws_account_id, update_tag)
        data = get_instance_patches(boto3_session, region, instance_ids)
        load_instance_patches(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ssm(neo4j_session, common_job_parameters)

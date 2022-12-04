import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.intel.gcp import compute
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_gcp_buckets(storage: Resource, project_id: str, common_job_parameters) -> Dict:
    """
    Returns a list of storage objects within some given project

    :type storage: The GCP storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The Google Project Id that you are retrieving buckets from

    :rtype: Storage Object
    :return: Storage response object
    """
    try:
        req = storage.buckets().list(project=project_id)
        res = req.execute()
        for item in res.get('items', []):
            acl = item.get('acl', [])
            for item2 in acl:
                item['entity'] = item2.get('entity', None)
            defaultObjectAcl = item.get('defaultObjectAcl', [])
            for item3 in defaultObjectAcl:
                item['defaultentity'] = item3.get('entity', None)
        if common_job_parameters.get('pagination', {}).get('storage', None):
            pageNo = common_job_parameters.get("pagination", {}).get("storage", None)["pageNo"]
            pageSize = common_job_parameters.get("pagination", {}).get("storage", None)["pageSize"]
            totalPages = len(res.get('items', [])) / pageSize
            if int(totalPages) != totalPages:
                totalPages = totalPages + 1
            totalPages = int(totalPages)
            if pageNo < totalPages or pageNo == totalPages:
                logger.info(f'pages process for storage buckets {pageNo}/{totalPages} pageSize is {pageSize}')
            page_start = (
                common_job_parameters.get('pagination', {}).get('storage', None)[
                    'pageNo'
                ] - 1
            ) * common_job_parameters.get('pagination', {}).get('storage', None)['pageSize']
            page_end = page_start + common_job_parameters.get('pagination', {}).get('storage', None)['pageSize']
            if page_end > len(res.get('items', [])) or len(res.get('items', [])) == page_end:
                res['items'] = res.get('items', [])[page_start:]
            else:
                has_next_page = True
                res['items'] = res.get('items', [])[page_start:page_end]
                common_job_parameters['pagination']['storage']['hasNextPage'] = has_next_page
        return res
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == 'invalid':
            logger.warning(
                (
                    "The project %s is invalid - returned a 400 invalid error."
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return {}
        elif reason == 'forbidden':
            logger.warning(
                (
                    "You do not have storage.bucket.list access to the project %s. "
                    "Full details: %s"
                ), project_id, e, )
            return {}
        else:
            raise


@timeit
def transform_gcp_buckets(bucket_res: Dict, project_id: str, regions: list) -> List[Dict]:
    '''
    Transform the GCP Storage Bucket response object for Neo4j ingestion

    :type bucket_res: The GCP storage resource object (https://cloud.google.com/storage/docs/json_api/v1/buckets)
    :param bucket_res: The return data

    :rtype: list
    :return: List of buckets ready for ingestion to Neo4j
    '''

    bucket_list = []
    for b in bucket_res.get('items', []):
        bucket = {}
        bucket['etag'] = b.get('etag')
        bucket['iam_config_bucket_policy_only'] = \
            b.get('iamConfiguration', {}).get('bucketPolicyOnly', {}).get('enabled', None)
        bucket['id'] = f"projects/{project_id}/locations/{str(b['location']).lower()}/buckets/{b['name']}"
        bucket['name'] = b['name']
        bucket['labels'] = [(key, val) for (key, val) in b.get('labels', {}).items()]
        bucket['owner_entity'] = b.get('owner', {}).get('entity')
        bucket['owner_entity_id'] = b.get('owner', {}).get('entityId')
        bucket['kind'] = b.get('kind')
        bucket['location'] = b.get('location', "").lower()
        x = bucket['location'].split("-")
        bucket['region'] = x[0]
        if len(x) > 1:
            bucket['region'] = f"{x[0]}-{x[1]}"
        bucket['location_type'] = b.get('locationType')
        bucket['meta_generation'] = b.get('metageneration', None)
        bucket['project_number'] = b['projectNumber']
        bucket['self_link'] = b.get('selfLink')
        bucket['storage_class'] = b.get('storageClass')
        bucket['time_created'] = b.get('timeCreated')
        bucket['updated'] = b.get('updated')
        bucket['entity'] = b.get('entity', None)
        bucket['defaultentity'] = b.get('defaultentity', None)
        bucket['uniform_bucket_level_access'] = b.get('iamConfiguration', {}).get(
            'uniformBucketLevelAccess', {},
        ).get('enabled', None)
        bucket['versioning_enabled'] = b.get('versioning', {}).get('enabled', None)
        bucket['default_event_based_hold'] = b.get('defaultEventBasedHold', None)
        bucket['retention_period'] = b.get('retentionPolicy', {}).get('retentionPeriod', None)
        bucket['default_kms_key_name'] = b.get('encryption', {}).get('defaultKmsKeyName')
        bucket['log_bucket'] = b.get('logging', {}).get('logBucket')
        bucket['requester_pays'] = b.get('billing', {}).get('requesterPays', None)
        bucket['consolelink'] = gcp_console_link.get_console_link(resource_name='storage_bucket', bucket_name=b['name'])

        if regions is None:
            bucket_list.append(bucket)

        else:
            if bucket['region'] in regions:
                bucket_list.append(bucket)

    return bucket_list


@timeit
def load_gcp_buckets(neo4j_session: neo4j.Session, buckets: List[Dict], gcp_update_tag: int) -> None:
    '''
    Ingest GCP Storage Buckets to Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type buckets: list
    :param buckets: List of GCP Storage Buckets to ingest

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    '''

    query = """
    MERGE (p:GCPProject{id: $ProjectNumber})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $gcp_update_tag

    MERGE (bucket:GCPBucket{id:  $BucketId})
    ON CREATE SET bucket.firstseen = timestamp(),
    bucket.bucket_id = $BucketId
    SET bucket.self_link = $SelfLink,
    bucket.project_number = $ProjectNumber,
    bucket.kind = $Kind,
    bucket.name = $name,
    bucket.location = $Location,
    bucket.region = $region,
    bucket.location_type = $LocationType,
    bucket.meta_generation = $MetaGeneration,
    bucket.storage_class = $StorageClass,
    bucket.time_created = $TimeCreated,
    bucket.entity = $Entity,
    bucket.defaultentity = $DefaultEntity,
    bucket.uniform_bucket_level_access = $UniformBucketLevelAccess,
    bucket.retention_period = $RetentionPeriod,
    bucket.iam_config_bucket_policy_only = $IamConfigBucketPolicyOnly,
    bucket.owner_entity = $OwnerEntity,
    bucket.owner_entity_id = $OwnerEntityId,
    bucket.versioning_enabled = $VersioningEnabled,
    bucket.log_bucket = $LogBucket,
    bucket.requester_pays = $RequesterPays,
    bucket.default_kms_key_name = $DefaultKmsKeyName,
    bucket.consolelink = $consolelink,
    bucket.lastupdated = $gcp_update_tag

    MERGE (p)-[r:RESOURCE]->(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for bucket in buckets:
        neo4j_session.run(
            query,
            ProjectNumber=bucket['project_number'],
            BucketId=bucket['id'],
            SelfLink=bucket['self_link'],
            Kind=bucket['kind'],
            Location=bucket['location'],
            region=bucket['region'],
            LocationType=bucket['location_type'],
            MetaGeneration=bucket['meta_generation'],
            StorageClass=bucket['storage_class'],
            TimeCreated=bucket['time_created'],
            Entity=bucket['entity'],
            DefaultEntity=bucket['defaultentity'],
            UniformBucketLevelAccess=bucket['uniform_bucket_level_access'],
            RetentionPeriod=bucket['retention_period'],
            IamConfigBucketPolicyOnly=bucket['iam_config_bucket_policy_only'],
            OwnerEntity=bucket['owner_entity'],
            OwnerEntityId=bucket['owner_entity_id'],
            VersioningEnabled=bucket['versioning_enabled'],
            LogBucket=bucket['log_bucket'],
            RequesterPays=bucket['requester_pays'],
            DefaultKmsKeyName=bucket['default_kms_key_name'],
            consolelink=bucket['consolelink'],
            name=bucket['name'],
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_buckets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Storage Bucket nodes and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_storage_bucket_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, storage: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    """
    Get GCP instances using the Storage resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type storage: The storage resource object created by googleapiclient.discovery.build()
    :param storage: The GCP Storage resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing Storage for project '%s', at %s.", project_id, tic)

    logger.info("Syncing Storage objects for project %s.", project_id)
    storage_res = get_gcp_buckets(storage, project_id, common_job_parameters)
    bucket_list = transform_gcp_buckets(storage_res, project_id, regions)
    load_gcp_buckets(neo4j_session, bucket_list, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_buckets(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, bucket_list, gcp_update_tag, common_job_parameters, 'buckets', 'GCPBucket')

    toc = time.perf_counter()
    logger.info(f"Time to process Storage: {toc - tic:0.4f} seconds")

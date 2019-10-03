import logging
from googleapiclient.discovery import HttpError

from cartography.intel.gcp import compute
logger = logging.getLogger(__name__)


def get_gcp_bucket_metadata(storage, bucket):
    """
    Retrieves metadata about the given bucket

    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type bucket: str
    :param bucket: Google Cloud Bucket name

    :rtype: dict
    :return: Metadata for specified bucket
    """
    try:
        req = storage.buckets().get(bucket=bucket)
        res = req.execute()
        return res
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == 'notFound':
            logger.debug(
                ("The bucket %s was not found - returned a 404 not found error."
                 "Full details: %s"), bucket, e, )
            return None
        elif reason == 'forbidden':
            logger.debug(
                ("You do not have storage.bucket.get access to the bucket %s. "
                 "Full details: %s"), bucket, e, )
            return None
        else:
            raise


def get_gcp_buckets(storage, project):
    """
    Returns a list of storage objects within some given project

    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type project: str
    :param project: The Google Project name that you are retrieving buckets from
    :rtype: Storage Object
    :return: Storage response object
    """
    try:
        req = storage.buckets().list(project=project)
        res = req.execute()
        return res
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == 'invalid':
            logger.debug(
                (
                    "The project %s is invalid - returned a 400 invalid error."
                    "Full details: %s"
                ),
                project,
                e,
            )
            return None
        elif reason == 'forbidden':
            logger.debug(
                ("You do not have storage.bucket.list access to the project %s. "
                 "Full details: %s"), project, e, )
            return None
        else:
            raise


def get_gcp_bucket_iam_policy(storage, bucket):
    """
    Retrieves IAM policy about the given bucket.

    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type bucket: str
    :param bucket: Google Cloud Bucket name

    :rtype: dict
    :return: IAM Policy for specified bucket
    """
    try:
        req = storage.buckets().getIamPolicy(bucket=bucket)
        res = req.execute()
        return res
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == 'notFound':
            logger.debug(
                ("The bucket %s was not found - returned a 404 not found error."
                 "Full details: %s"), bucket, e, )
            return None
        elif reason == 'forbidden':
            logger.debug(
                ("You do not have storage.bucket.getIamPolicy access to the bucket %s. "
                 "Full details: %s"), bucket, e, )
            return None
        else:
            raise


def transform_gcp_buckets(bucket_res): 
    '''
    Transform the GCP Storage Bucket response object for Neo4j ingestion
    
    :type bucket_res: A storage resource object (https://cloud.google.com/storage/docs/json_api/v1/buckets) 
    :param bucket_res: The return data
    
    :rtype: list
    :return: List of buckets ready for ingestion to Neo4j
    '''
    
    bucket_list = []
    for b in bucket_res.get('items', []):
        bucket = {}
        bucket['etag'] = b.get('etag', '')  
        bucket['iam_config_bucket_policy_only'] = b.get('iamConfiguration'
                                                        , {}).get('bucketPolicyOnly', {}).get('enabled', None)
        bucket['iam_config_uniform_bucket_level_access'] = b.get('iamConfiguration'
                                                                 , {}).get('uniformBucketLevelAccess', {}).get('enabled', None)
        bucket['id'] = b.get('id', '') 
        bucket['labels'] = [(key, val) for (key, val) in b.get('labels', {}).items()] 
        bucket['owner_entity'] = b.get('owner', {}).get('entity', '') 
        bucket['owner_entity_id'] = b.get('owner', {}).get('entityId', '') 
        bucket['kind'] = b.get('kind', '') 
        bucket['location'] = b.get('location', '') 
        bucket['location_type'] = b.get('locationType', '')
        bucket['meta_generation'] = g.get('metageneration', None) 
        bucket['project_number'] = b.get('projectNumber', None) 
        bucket['self_link'] = b.get('selfLink', '') 
        bucket['storage_class'] = b.get('storageClass', '')
        bucket['time_created'] = b.get('timeCreated', '') 
        bucket['updated'] = b.get('updated', '') 
        bucket['versioning_enabled'] = b.get('versioning', {}).get('enabled', None) 
        bucket['default_event_based_hold']  = b.get('defaultEventBasedHold', None) 
        bucket['retention_period'] = b.get('retentionPolicy', {}).get('retentionPeriod', None) 
        bucket['default_kms_key_name'] = b.get('encryption', {}).get('defaultKmsKeyName', '') 
        bucket['log_bucket'] = b.get('logging', {}).get('logBucket', '') 
        bucket['requester_pays'] = b.get('billing', {}).get('requesterPays', None)  
        bucket_list.append(bucket)
    return bucket_list


def load_gcp_buckets(neo4j_session, buckets, gcp_update_tag): 
    '''
    Ingest GCP Storage Buckets to Neo4j
    
    :type neo4j_session: Neo4j session object 
    :param neo4j session: The Neo4j session object
    
    :type buckets: list
    :param buckets: List of GCP Buckets to injest 
    
    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    
    :rtype: NoneType
    :return: Nothing 
    '''
    
    query = """
    MERGE(p:GCPProject{projectnumber:{ProjectNumber}}) 
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {gcp_update_tag}
    
    MERGE(bucket:GCPBuckets{id:{BucketId}})
    ON CREATE SET bucket.firstseen = timestamp(),
    SET bucket.self_link = {SelfLink},
    bucket.id = {BucketId}, 
    bucket.project_number = {ProjectNumber}, 
    bucket.kind = {Kind}, 
    bucket.location = {Location}, 
    bucket.location_type = {LocationType}, 
    bucket.meta_generation = {MetaGeneration}, 
    bucket.storage_class = {StorageClass}, 
    bucket.time_created = {TimeCreated}, 
    bucket.retention_period = {RetentionPeriod}, 
    bucket.iam_config_bucket_policy_only = {IamConfigBucketPolicyOnly}, 
    bucket.iam_config_uniform_bucket_level_access = {IamConfigUniformBucketLevelAccess}, 
    bucket.owner_entity = {OwnerEntity}, 
    bucket.owner_entity_id = {OwnerEntityId},
    bucket.lastupdated = {gcp_update_tag}, 
    bucket.versioning_enabled = {VersioningEnabled}, 
    bucket.log_bucket = {LogBucket}, 
    bucket.requester_pays = {RequesterPays}, 
    bucket.default_kms_key_name = {DefaultKmsKeyName}
    
    MERGE (p)-[r:RESOURCE]->(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {gcp_update_tag}
    """
    for bucket in buckets:
        neo4j_session.run(
            query,
            ProjectNumber=bucket['project_number'],
            BucketId=bucket['id'], 
            SelfLink=bucket['self_link'],
            Kind=bucket['kind'], 
            Location=bucket['location'],
            LocationType=bucket['location_type'],
            MetaGeneration=bucket['meta_generation'],
            StorageClass=bucket['storage_class'],
            TimeCreated=bucket['time_created'],
            RetentionPeriod=bucket['retention_period'],
            IamConfigBucketPolicyOnly=bucket['iam_config_bucket_policy_only'],
            IamConfigUniformBucketLevelAccess=bucket['iam_config_uniform_bucket_level_access'],
            OwnerEntity=bucket['owner_entity'],
            OwnerEntityId=bucket['owner_entity_id'],
            VersioningEnabled=bucket['versioning_enabled'], 
            LogBucket=bucket['log_bucket'], 
            RequesterPays=bucket['requester_pays'], 
            DefaultKmsKeyName=bucket['default_kms_key_name'],
            gcp_update_tag=gcp_update_tag,
        )

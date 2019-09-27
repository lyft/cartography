import logging
from collections import namedtuple

import googleapiclient.discovery
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.intel.gcp import compute
logger = logging.getLogger(__name__)


def get_bucket_metadata(storage, bucket):
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


def get_buckets(storage, project):
    """
    Returns a list of storage objects within some given project

    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type project: str
    :param project: The Google Project name that you are retrieving buckets from
    :rtype: list
    :return: List of storage objects
    """
    try:
        req = storage.buckets().list(project=project)
        res = req.execute()
        all_objects = []
        all_objects.extend(res.get('items', []))
        return all_objects
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


def get_bucket_iam_policy(storage, bucket):
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
    
    :type bucket_res: A storage resource object
    :param bucket_res: The return data
    
    :rtype: list
    :return: List of buckets ready for ingestion to Neo4j
    '''
    #TODO: Verify data type of each value corresponding to some field (from gcp storage object response) 
    bucket_list = []
    for b in bucket_res.get('items', []):
        bucket = {}
        bucket['etag'] = b.get('etag', '')  
        bucket['iam_config_bucket_policy_only'] = b.get('iamConfiguration', {}).get('bucketPolicyOnly', {}).get('enabled', None)
        bucket['iam_config_uniform_bucket_level_access'] = b.get('iamConfiguration', {}).get('uniformBucketLevelAccess', {}).get('enabled', None)
        bucket['id'] = b.get('id', '') 
        bucket['kind'] = b.get('kind', '') 
        bucket['location'] = b.get('location', '') 
        bucket['location_type'] = b.get('locationType', '')
        bucket['meta_generation'] = g.get('metageneration', '') 
        bucket['name'] = b.get('name', '')
        bucket['project_number'] = b.get('projectNumber', '') 
        bucket['self_link'] = b.get('selfLink', '') 
        bucket['storage_class'] = b.get('storageClass', '')
        bucket['time_created'] = b.get('timeCreated', '') 
        bucket['updated'] = b.get('updated', '') 
        bucket_list.append(bucket)
    return bucket_list

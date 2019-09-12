import logging
from collections import namedtuple

import googleapiclient.discovery
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.intel.gcp import compute
    

def get_bucket_metadata(storage, bucket, credentials):
    """
    Retrieves metadata about the given bucket
    
    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()
    
    :type bucket: str
    :param bucket: Google Cloud Bucket name
    
    :type credentials: A GoogleCredentials object 
    :param credentials: The GoogleCredentials object used for authentication 
    
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
                (
                    "The bucket %s was not found - returned a 404 not found error."
                    "Full details: %s"
                ),
                bucket,
                e,
            )
            return None
        elif reason == 'forbidden':
            logger.debug(
                (
                    "You do not have storage.bucket.get access to the bucket %s. "
                    "Full details: %s"
                ),
                bucket,
                e,
            )
            return None
        else:
            raise


def list_buckets(storage, project, credentials):
    """
    Returns a list of storage objects within some given project
    
    :type storage: A storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()
    
    :type project: str 
    :param project: The Google Project name that you are retrieving buckets from
    
    :type credentials: A GoogleCredentials object 
    :param credentials: The GoogleCredentials object used for authentication 
    
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
                (
                    "You do not have storage.bucket.list access to the project %s. "
                    "Full details: %s"
                ),
                project,
                e,
            )
            return None
        else:
            raise

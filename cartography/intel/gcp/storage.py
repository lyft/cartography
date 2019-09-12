import logging
from collections import namedtuple

import googleapiclient.discovery
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials


def create_storage_client(credentials):
    '''
    Instantiates a Google Cloud Bucket Resource
    
    :param credentials: The GoogleCredentials object
    :return: A Google Cloud Bucket Resource Object
    '''
    return googleapiclient.discovery.build('storage', 'v1', credentials=credentials)
    

def get_bucket_metadata(bucket, credentials):
    """
    Retrieves metadata about the given bucket
    
    :param bucket: Google Cloud Bucket object
    :param credentials: The GoogleCredentials object
    :return: Metadata for specified bucket
    """
    service = create_storage_client(credentials)
    req = service.buckets().get(bucket=bucket)
    return req.execute()


def list_buckets(project, credentials):
    """
    Returns a list of storage objects within some given project
    
    :param project: The Google Project name that you are retrieving buckets from
    :param credentials: The GoogleCredentials object
    :return: List of storage objects
    """
    service = create_storage_client(credentials)
    req = service.buckets().list(project=project)
    res = req.execute()
    
    all_objects = []
    all_objects.extend(res.get('items', []))
    return all_objects

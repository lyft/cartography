import base64
import json
import logging
import os
from collections import namedtuple

import googleapiclient.discovery
import httplib2
import neo4j
from googleapiclient.discovery import Resource
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.config import Config
from cartography.intel.gsuite import api
from cartography.util import timeit

OAUTH_SCOPE = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member',
]

logger = logging.getLogger(__name__)

Resources = namedtuple('Resources', 'admin')


def _get_admin_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google API resource object to call the Google API.
    Used to pull users and groups.  See https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param credentials: The GoogleCredentials object
    :return: An admin api resource object
    """
    return googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials: GoogleCredentials) -> Resources:
    """
    Create namedtuple of all resource objects necessary for Google API data gathering.
    :param credentials: The GoogleCredentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        admin=_get_admin_resource(credentials),
    )


@timeit
def start_gsuite_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the GSuite ingestion process by initializing

    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    if config.gsuite_auth_method == 'delegated':  # Legacy delegated method
        logger.info('Attempting to authenticate to GSuite using legacy delegated method')
        try:
            credentials = GoogleCredentials.from_stream(config.gsuite_config)
            credentials = credentials.create_scoped(OAUTH_SCOPE)
            credentials = credentials.create_delegated(os.environ.get('GSUITE_DELEGATED_ADMIN'))

        except ApplicationDefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    'Gsuite data then you can ignore this message. Otherwise, the error code is: %s '
                    'Make sure your GSuite credentials file (if any) is valid. '
                    'For more details see README'
                ),
                e,
            )
            return
    elif config.gsuite_auth_method == 'oauth':
        auth_tokens = json.loads(str(base64.b64decode(config.gsuite_config).decode()))
        logger.info('Attempting to authenticate to GSuite using OAuth')
        try:
            credentials = GoogleCredentials(
                None,
                auth_tokens['client_id'],
                auth_tokens['client_secret'],
                auth_tokens['refresh_token'],
                None,
                auth_tokens['token_uri'],
                'Cartography',
            )
            credentials.refresh(httplib2.Http())
            credentials = credentials.create_scoped(OAUTH_SCOPE)
        except ApplicationDefaultCredentialsError as e:
            logger.error(
                (
                    "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                    'Gsuite data then you can ignore this message. Otherwise, the error code is: %s '
                    'Make sure your GSuite credentials are configured correctly, your credentials are valid. '
                    'For more details see README'
                ),
                e,
            )
            return

    resources = _initialize_resources(credentials)
    api.sync_gsuite_users(neo4j_session, resources.admin, config.update_tag, common_job_parameters)
    api.sync_gsuite_groups(neo4j_session, resources.admin, config.update_tag, common_job_parameters)

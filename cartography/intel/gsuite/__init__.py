import logging
import os
from collections import namedtuple

import googleapiclient.discovery
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.intel.gsuite import api
from cartography.util import timeit

# GSuite Delegated admin e-mail https://developers.google.com/admin-sdk/directory/v1/guides/delegation
GSUITE_DELEGATED_ADMIN = os.environ.get('GSUITE_DELEGATED_ADMIN')
GSUITE_CREDS = os.environ.get('GSUITE_GOOGLE_APPLICATION_CREDENTIALS')

OAUTH_SCOPE = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member',
]

logger = logging.getLogger(__name__)

Resources = namedtuple('Resources', 'admin')


def _get_admin_resource(credentials):
    """
    Instantiates a Google API resource object to call the Google API.
    Used to pull users and groups.  See https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param credentials: The GoogleCredentials object
    :return: An admin api resource object
    """
    return googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials):
    """
    Create namedtuple of all resource objects necessary for Google API data gathering.
    :param credentials: The GoogleCredentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        admin=_get_admin_resource(credentials),
    )


@timeit
def start_gsuite_ingestion(session, config):
    """
    Starts the GSuite ingestion process by initializing

    :param session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    try:
        credentials = GoogleCredentials.from_stream(GSUITE_CREDS)
        credentials = credentials.create_scoped(OAUTH_SCOPE)
        credentials = credentials.create_delegated(GSUITE_DELEGATED_ADMIN)

    except ApplicationDefaultCredentialsError as e:
        logger.debug('Error occurred calling GoogleCredentials.get_application_default().', exc_info=True)
        logger.error(
            (
                "Unable to initialize GSuite creds. If you don't have GSuite data or don't want to load "
                'Gsuite data then you can ignore this message. Otherwise, the error code is: %s '
                'Make sure your GSuite credentials are configured correctly, your credentials file (if any) is valid. '
                'For more details see README'
            ),
            e,
        )
        return

    resources = _initialize_resources(credentials)
    api.sync_gsuite_users(session, resources.admin, config.update_tag, common_job_parameters)
    api.sync_gsuite_groups(session, resources.admin, config.update_tag, common_job_parameters)

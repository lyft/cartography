import logging
from collections import namedtuple

import googleapiclient.discovery
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from cartography.intel.gsuite import api


OAUTH_SCOPE = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.group',
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
        # Explicitly use Application Default Credentials.
        # See https://oauth2client.readthedocs.io/en/latest/source/
        #             oauth2client.client.html#oauth2client.client.OAuth2Credentials
        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(OAUTH_SCOPE)
        credentials = credentials.create_delegated('cartography-admin@lyft.com')

    except ApplicationDefaultCredentialsError as e:
        logger.debug('Error occurred calling GoogleCredentials.get_application_default().', exc_info=True)
        logger.error(
            (
                "Unable to initialize Google Compute Platform creds. If you don't have GCP data or don't want to load "
                'GCP data then you can ignore this message. Otherwise, the error code is: %s '
                'Make sure your GCP credentials are configured correctly, your credentials file (if any) is valid, and '
                'that the identity you are authenticating to has the securityReviewer role attached.'
            ),
            e,
        )
        return

    resources = _initialize_resources(credentials)
    api.sync_gsuite_users(session, resources.admin, config.update_tag, common_job_parameters)
    api.sync_gsuite_groups(session, resources.admin, config.update_tag, common_job_parameters)

import base64
import json
import logging

import neo4j
from requests_oauthlib import OAuth1Session

import cartography.intel.clevercloud.addons
import cartography.intel.clevercloud.applications
import cartography.intel.clevercloud.organization
import cartography.intel.clevercloud.users
from cartography.config import Config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_clevercloud_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Clevercloud data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.clevercloud_config:
        logger.info(
            'Clevercloud import is not configured - skipping this module.'
            'See docs to configure.',
        )
        return
    auth_tokens = json.loads(base64.b64decode(config.clevercloud_config).decode())

    for organization in auth_tokens:
        logger.debug("Start ingest for %s", organization['org_id'])
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ORG_ID": organization['org_id'],
        }
        session = OAuth1Session(
            client_key=organization['consumer_key'],
            client_secret=organization['consumer_secret'],
            resource_owner_key=organization['client_key'],
            resource_owner_secret=organization['client_secret'],
            signature_method='HMAC-SHA512',
        )

        cartography.intel.clevercloud.users.sync(neo4j_session, session, common_job_parameters)
        cartography.intel.clevercloud.organization.sync(neo4j_session, session, common_job_parameters)
        cartography.intel.clevercloud.addons.sync(neo4j_session, session, common_job_parameters)
        cartography.intel.clevercloud.applications.sync(neo4j_session, session, common_job_parameters)

    # WIP: Doc

    run_cleanup_job(
        "clevercloud_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

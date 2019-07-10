import logging
import json
import requests
import requests.auth
import os

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

# API key for CRXcavator generaated from crxcavator.io portal
CRXcavator_API_KEY = os.environ.get('CREDENTIALS_CRXCAVATOR_API_KEY')

# API for the CRXcavator API - https://api.crxcavator.io/v1 as of 07/09/19
CRXcavator_API_BASE_URL = os.environ.get('CRXCAVATOR_URL')


def get_extensions():
    """
    Get all of the installed extension metadata
    :return: JSON text blob containing all extension metadata defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1extensions~1combined/get
    """
    return call_crxcavator_api("/group/extensions/combined")


def get_users_extensions():
    """
    Gets listing of all users who have installed each extension
    :return: JSON text blob containing user email to extension id mapping defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1users~1extensions/get
    """
    return call_crxcavator_api("/group/users/extensions")


def call_crxcavator_api(api_and_parameters):
    """
    Perform the call requested to the CRXcavator API
    :param api_and_parameters: Query string for the API including the required parameters
    :return: Returns JSON text blob for the API called. API spec is at https://crxcavator.io/apidocs
    """
    uri = CRXcavator_API_BASE_URL + api_and_parameters
    data = requests.get(
        uri,
        headers={'Accept': 'application/json',
                 'API-Key': CRXcavator_API_KEY})
    if data.ok:
        return data.json()
    else:
        logger.error('Error during CRXcavator API call {}'.format(data.status_code))
        return None


def ingest_extensions(session, update_tag):
    """
    Ingests the extension details into Neo4J
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """
    # the JSON returned from the CRXcavator API does not return well formatted objects
    # instead, each object is named after it's key, making enumeration more difficult
    # will build a cleaner object for import into graph

    _data_index = 1
    _row_index = 0

    extension_json = get_extensions()
    if not extension_json:
        logger.error('No extensions data returned')
        return
    ingestion_cypher = """
    UNWIND {ExtensionsData} as extension
    MERGE (e:ChromeExtension{id: extension.id})
    ON CREATE SET
    e.extension_id = extension.extension_id,
    e.version = extension.version,
    e.firstseen = timestamp()
    SET
    e.extcalls = extension.extcalls,
    e.risk_total = extension.risk_total,
    e.risk_metadata = extension.risk_metadata,
    e.address = extension.address,
    e.email = extension.email,
    e.icon = extension.icon,
    e.last_updated = extension.last_updated,
    e.name = extension.name,
    e.offered_by = extension.offered_by,
    e.permissions_warnings = extension.permissions_warnings,
    e.privacy_policy = extension.privacy_policy,
    e.rating = extension.rating,
    e.rating_users = extension.rating_users,
    e.short_description = extension.short_description,
    e.size = extension.size,
    e.support_site = extension.support_site,
    e.users = extension.users,
    e.website = extension.website,
    e.type = extension.type,
    e.price = extension.price,
    e.offline_enabled = extension.offline_enabled,
    e.lastupdated = {UpdateTag}
    """

    extensions = []
    for extension in extension_json.items():
        details = extension[_data_index][_row_index]
        if not details:
            continue
        extension_id = details['extension_id']
        version = details['version']
        data = details['data']
        # permissions warnings can be a list or null, if list concat to a single string
        permission_warnings = data['webstore'].get('permission_warnings')
        if permission_warnings:
            permission_warnings = ', '.join(permission_warnings)
        extensions.append({
            'id': "{0}|{1}".format(extension_id, version),
            'extension_id': extension_id,
            'version': version,
            'risk_total': data['risk'].get('total'),
            'risk_metadata': json.dumps(data['risk'].get('metadata')),
            'address': data['webstore'].get('address'),
            'email': data['webstore'].get('email'),
            'icon': data['webstore'].get('icon'),
            'last_updated': data['webstore'].get('last_updated'),
            'name': data['webstore'].get('name'),
            'offered_by': data['webstore'].get('offered_by'),
            'permissions_warnings': permission_warnings,
            'privacy_policy': data['webstore'].get('privacy_policy'),
            'rating': data['webstore'].get('rating'),
            'rating_users': data['webstore'].get('rating_users'),
            'short_description': data['webstore'].get('short_description'),
            'size': data['webstore'].get('size'),
            'support_site': data['webstore'].get('support_site'),
            'users': data['webstore'].get('users'),
            'website': data['webstore'].get('website'),
            'type': data['webstore'].get('type'),
            'price': data['webstore'].get('price')
        })
    logger.info('Ingesting {} extensions'.format(len(extensions)))
    session.run(ingestion_cypher, ExtensionsData=extensions, UpdateTag=update_tag)


def ingest_users_extensions(session, update_tag):
    """
    Ingests the extension to user mapping details into Neo4J
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """
    user_extensions_json = get_users_extensions()
    if not user_extensions_json:
        logger.error('Failed to get user data from CRXcavator')
        return
    # todo: once G Suite ingestion is created, move first MERGE to that process
    user_ingestion_cypher = """
    UNWIND {Users} as user_email
    MERGE (user:GSuiteUser{id: user_email, email: user_email})
    ON CREATE SET
    user.firstseen = timestamp()
    SET user.lastupdated = {UpdateTag}
    """
    # todo: add relationship to computer node when JAMF data is moved to Cartography
    extension_ingestion_cypher = """
    UNWIND {ExtensionsUsers} as extension_user
    MATCH (user:GSuiteUser{email: extension_user.user}),(ext:ChromeExtension{id:extension_user.id})
    MERGE (user)-[r:INSTALLS]->(ext)
    ON CREATE SET
    r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    user_extensions = user_extensions_json.items()
    users_set = set()
    extensions_by_user = []
    for extension in user_extensions:
        for details in extension[1].items():
            for user in details[1]['users']:
                users_set.add(user)
                extensions_by_user.append({
                    'id': "{0}|{1}".format(extension[0], details[0]),
                    'user': user})
    users = list(users_set)
    logger.info('Ingesting {} users'.format(len(users)))
    session.run(user_ingestion_cypher, Users=users, UpdateTag=update_tag)
    logger.info('Ingesting {} user->extension relationships'.format(len(extensions_by_user)))
    session.run(extension_ingestion_cypher, ExtensionsUsers=extensions_by_user, UpdateTag=update_tag)


def start_extension_ingestion(session, config):
    """
    If this module is configured, perform ingestion of CRXcavator data. Otherwise warn and exit
    :param session: Neo4J session for database interface
    :param config: Neo4J server URI and Update tag for data freshness
    :return: None
    """
    if not CRXcavator_API_BASE_URL or not CRXcavator_API_KEY:
        logger.warning('CRXcavator import is not configured - skipping this module')
        return None

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    ingest_extensions(session, common_job_parameters['UPDATE_TAG'])
    ingest_users_extensions(session, common_job_parameters['UPDATE_TAG'])
    run_cleanup_job(
        'crxcavator_import_cleanup.json',
        session,
        common_job_parameters
    )

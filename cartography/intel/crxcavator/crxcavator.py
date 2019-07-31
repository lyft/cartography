import json
import logging

import requests.auth

logger = logging.getLogger(__name__)


def get_extensions(crxcavator_api_key, crxcavator_base_url):
    """
    Get all of the installed extension metadata
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: JSON text blob containing all extension metadata defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1extensions~1combined/get
    """
    return call_crxcavator_api("/group/extensions/combined", crxcavator_api_key, crxcavator_base_url)


def get_users_extensions(crxcavator_api_key, crxcavator_base_url):
    """
    Gets listing of all users who have installed each extension
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: JSON text blob containing user email to extension id mapping defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1users~1extensions/get
    """
    return call_crxcavator_api("/group/users/extensions", crxcavator_api_key, crxcavator_base_url)


def call_crxcavator_api(api_and_parameters, crxcavator_api_key, crxcavator_base_url):
    """
    Perform the call requested to the CRXcavator API
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :param api_and_parameters: Query string for the API including the required parameters
    :return: Returns JSON text blob for the API called. API spec is at https://crxcavator.io/apidocs
    """
    uri = crxcavator_base_url + api_and_parameters
    data = requests.get(
        uri,
        headers={
            'Accept': 'application/json',
            'API-Key': crxcavator_api_key,
        },
    )
    # if call failed, use requests library to raise an exception
    data.raise_for_status()
    return data.json()


def transform_extensions(extension_json):
    """
    Transforms the raw extensions JSON from the API into a list of extensions data
    :param extension_json:  The JSON text blob returned from the CRXcavator API
    :return: List containing extension info for ingestion
    """
    # the JSON returned from the CRXcavator API does not return well formatted objects
    # instead, each object is named after it's key, making enumeration more difficult
    # will build a cleaner object for import into graph

    _data_index = 1
    _row_index = 0

    extensions = []
    for extension in extension_json.items():
        details = extension[_data_index][_row_index]
        if not details:
            logger.warning(f'Could not retrieve details for extension {extension}')
            continue
        extension_id = details['extension_id']
        version = details['version']
        data = details['data']
        extensions.append({
            'id': f"{extension_id}|{version}",
            'extension_id': extension_id,
            'version': version,
            'risk_total': data['risk'].get('total'),
            'risk_metadata': json.dumps(data['risk'].get('metadata')),
            'address': data['webstore'].get('address'),
            'email': data['webstore'].get('email'),
            'icon': data['webstore'].get('icon'),
            'crxcavator_last_updated': data['webstore'].get('last_updated'),
            'name': data['webstore'].get('name'),
            'offered_by': data['webstore'].get('offered_by'),
            'permissions_warnings': data['webstore'].get('permission_warnings'),
            'privacy_policy': data['webstore'].get('privacy_policy'),
            'rating': data['webstore'].get('rating'),
            'rating_users': data['webstore'].get('rating_users'),
            'short_description': data['webstore'].get('short_description'),
            'size': data['webstore'].get('size'),
            'support_site': data['webstore'].get('support_site'),
            'users': data['webstore'].get('users'),
            'website': data['webstore'].get('website'),
            'type': data['webstore'].get('type'),
            'price': data['webstore'].get('price'),
            'report_link': "https://crxcavator.io/report/" + extension_id + "/" + version,
        })
    return extensions


def load_extensions(extensions, session, update_tag):
    """
    Ingests the extension details into Neo4J
    :param extensions: List of extension data to load to Neo4J
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """
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
    e.crxcavator_last_updated = extension.crxcavator_last_updated,
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
    e.report_link = extension.report_link,
    e.lastupdated = {UpdateTag}
    """

    logger.info('Ingesting {} extensions'.format(len(extensions)))
    session.run(ingestion_cypher, ExtensionsData=extensions, UpdateTag=update_tag)


def transform_user_extensions(user_extension_json):
    """
    Transforms the raw extensions JSON from the API into a list of extensions mapped to users
    :param user_extension_json:  The JSON text blob returned from the CRXcavator API
    :return: Tuple containing unique users list and extension info for ingestion
    """
    user_extensions = user_extension_json.items()
    users_set = set()
    extensions_by_user = []
    for extension in user_extensions:
        for details in extension[1].items():
            for user in details[1]['users']:
                users_set.add(user)
                extensions_by_user.append({
                    'id': "{}|{}".format(extension[0], details[0]),
                    'user': user,
                })
    if len(users_set) == 0:
        raise ValueError('No users returned from CRXcavator')
    if len(extensions_by_user) == 0:
        raise ValueError('No user->extension mapping returned from CRXcavator')

    return list(users_set), extensions_by_user


def load_user_extensions(users, extensions_by_user, session, update_tag):
    """
    Ingests the extension to user mapping details into Neo4J
    :param users: List of user objects to create for mapping
    :param extensions_by_user: List of user to extension id mappings
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """

    user_ingestion_cypher = """
    UNWIND {Users} as user_email
    MERGE (user:GSuiteUser{id: user_email, email: user_email})
    ON CREATE SET
    user.firstseen = timestamp()
    SET user.lastupdated = {UpdateTag}
    """

    extension_ingestion_cypher = """
    UNWIND {ExtensionsUsers} as extension_user
    MATCH (user:GSuiteUser{email: extension_user.user}),(ext:ChromeExtension{id:extension_user.id})
    MERGE (user)-[r:INSTALLS]->(ext)
    ON CREATE SET
    r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    logger.info('Ingesting {} users'.format(len(users)))
    session.run(user_ingestion_cypher, Users=users, UpdateTag=update_tag)
    logger.info('Ingesting {} user->extension relationships'.format(len(extensions_by_user)))
    session.run(extension_ingestion_cypher, ExtensionsUsers=extensions_by_user, UpdateTag=update_tag)


def sync_extensions(session, common_job_parameters, crxcavator_api_key, crxcavator_base_url):
    """
    Performs the sequential tasks to collect, transform, and sync extension data
    :param session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: None
    """
    extension_json = get_extensions(crxcavator_api_key, crxcavator_base_url)
    extensions = transform_extensions(extension_json)
    load_extensions(extensions, session, common_job_parameters['UPDATE_TAG'])

    user_extensions_json = get_users_extensions(crxcavator_api_key, crxcavator_base_url)
    users, user_extensions = transform_user_extensions(user_extensions_json)
    load_user_extensions(users, user_extensions, session, common_job_parameters['UPDATE_TAG'])

import json
import logging

import requests.auth
from requests import exceptions

logger = logging.getLogger(__name__)


def get_extension_details(crxcavator_api_key, crxcavator_base_url, extension_id, version):
    """
    Get metadata for the specific extension_id and version number provided
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :param extension_id: The extension id to request metadata for
    :param version: The version number of the extension to request metadata for
    :return: JSON text blob containing all extension metadata defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1extensions~1combined/get
    """
    return call_crxcavator_api(f"/report/{extension_id}/{version}", crxcavator_api_key, crxcavator_base_url)


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


def get_extensions(crxcavator_api_key, crxcavator_base_url, extensions_list):
    """
    Retrieves the detailed information for all the extension_id and version pairs
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :param extensions_list: list of dictonary items containing the extension_id and version pairs
    :return: list containing all metadata for extensions
    """
    extensions_details = []
    for extension in extensions_list:
        extension_id = extension['extension_id']
        version = extension['version']
        name = extension['name']
        try:
            details = get_extension_details(crxcavator_api_key, crxcavator_base_url, extension_id, version)
            if not details:
                # we only have the name and version from group API, create minimal version
                logger.debug(
                    f"CRXcavator ingest - No results returned from report API for "
                    f"extension {extension_id} {version}",
                )
                details = {
                    'data': dict(
                        webstore={
                            'name': name,
                        },
                    ), 'extension_id': extension_id, 'version': version,
                }
            extensions_details.append(details)
        except exceptions.RequestException as e:
            logger.info(f"CRXcavator ingest - API error retrieving details for extension {extension_id}", e)
    return extensions_details


def transform_extensions(extension_details):
    """
    Transforms the raw extensions JSON from the API into a list of extensions data
    :param extension_details:  List containing the extension details
    :return extension: List containing extension info for ingestion
    :return permissions: Unique list of permissions returned from crxcavator
    :return extension_permissions: Dictionary linking extensions to permissions
    """
    # the JSON returned from the CRXcavator API does not return well formatted objects
    # instead, each object is named after it's key, making enumeration more difficult
    # will build a cleaner object for import into graph

    extensions = []
    permissions_set = set()
    extensions_permissions = []
    for extension in extension_details:
        extension_id = extension['extension_id']
        version = extension['version']
        data = extension.get('data')
        if not data:
            logger.warning(f'CRXcavator ingest - Could not retrieve details for extension {extension}')
            continue
        risk = data.get('risk', {})
        webstore = data.get('webstore', {})
        manifest = data.get('manifest', {})
        permissions = manifest.get('permissions', {})
        for permission in permissions:
            if type(permission) is dict:
                parsed_permissions = parse_permissions_dict(permission)
                permissions_set.update(parsed_permissions)
                for sub_permission in parsed_permissions:
                    extensions_permissions.append({
                        'id': f"{extension_id}|{version}",
                        'permission': sub_permission,
                    })
                continue
            permissions_set.add(permission)
            extensions_permissions.append({
                'id': f"{extension_id}|{version}",
                'permission': permission,
            })
        extensions.append({
            'id': f"{extension_id}|{version}",
            'extension_id': extension_id,
            'version': version,
            'risk_total': risk.get('total', 0),
            'risk_permissions_score': get_risk_data(risk, 'permissions'),
            'risk_webstore_score': get_risk_data(risk, 'webstore'),
            'risk_metadata': json.dumps(risk.get('metadata')),
            'risk_optional_permissions_score': get_risk_data(risk, 'optional_permissions'),
            'risk_csp_score': get_risk_data(risk, 'csp'),
            'risk_extcalls_score': get_risk_data(risk, 'extcalls'),
            'risk_vuln_score': get_risk_data(risk, 'retire'),
            'address': webstore.get('address'),
            'email': webstore.get('email'),
            'icon': webstore.get('icon'),
            'crxcavator_last_updated': webstore.get('last_updated'),
            'name': webstore.get('name'),
            'offered_by': webstore.get('offered_by'),
            'permissions_warnings': webstore.get('permission_warnings'),
            'privacy_policy': webstore.get('privacy_policy'),
            'rating': webstore.get('rating'),
            'rating_users': webstore.get('rating_users'),
            'short_description': webstore.get('short_description'),
            'size': webstore.get('size'),
            'support_site': webstore.get('support_site'),
            'users': webstore.get('users'),
            'website': webstore.get('website'),
            'type': webstore.get('type'),
            'price': webstore.get('price'),
            'report_link': f"https://crxcavator.io/report/{extension_id}/{version}",
        })
    return extensions, list(permissions_set), extensions_permissions


def parse_permissions_dict(permissions_dict):
    """
    Parses the possible complex permissions objects into a list of objects
    Parsing cases based on results from crxcavator API as of October 2019
    :param permissions_dict: a dict object from the permissions key
    :return: a list of individual permissions
    """
    permissions = []
    usb_devices = permissions_dict.get('usbDevices', [])
    for device in usb_devices:
        permissions.append(f"usbdevice-{device.get('productId', 'none')}-{device.get('vendorId', 'none')}")
    filesystem = permissions_dict.get('fileSystem', [])
    for filesystem_permission in filesystem:
        permissions.append(f"filesystem-{filesystem_permission}")
    socket = permissions_dict.get('socket', [])
    for socket_permission in socket:
        permissions.append(f"socket-{socket_permission}")
    media_galleries = permissions_dict.get('mediaGalleries', [])
    for media in media_galleries:
        permissions.append(f"mediagalleries-{media}")
    if len(permissions) == 0:
        # this is a case not currently handled, so just log it and do not ingest it
        permission = json.dumps(permissions_dict)
        logger.warning(f"CRXcavator ingest - Unknown permissions dict type {permission}")
    return permissions


def get_risk_data(data_dict, key):
    """
    Gets the total risk value from the provided key and returns the value else 0
    :param data_dict: input data dictionary to parse
    :param key: key name to retrieve
    :return:
    """
    data = data_dict.get(key)
    data_score = data.get('total', 0) if data else 0
    return data_score


def load_extensions(extensions, permissions, extension_permissions, session, update_tag):
    """
    Ingests the extension details into Neo4J
    :param extensions: List of extension data to load to Neo4J
    :param permissions: unique list of extension permissions
    :param extension_permissions: Dictionary of extension-permission pairings
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """
    extensions_ingestion_cypher = """
    UNWIND {ExtensionsData} as extension
    MERGE (e:ChromeExtension{id: extension.id})
    ON CREATE SET
    e.extension_id = extension.extension_id,
    e.version = extension.version,
    e.firstseen = timestamp()
    SET
    e.extcalls = extension.extcalls,
    e.risk_total = extension.risk_total,
    e.risk_permissions_score = extension.risk_permissions_score,
    e.risk_metadata = extension.risk_metadata,
    e.risk_webstore_score = extension.risk_webstore_score,
    e.risk_optional_permissions_score = extension.risk_optional_permissions_score,
    e.risk_csp_score = extension.risk_csp_score,
    e.risk_extcalls_score = extension.risk_extcalls_score,
    e.risk_vuln_score = extension.risk_vuln_score,
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

    permissions_ingestion_cypher = """
    UNWIND {Permissions} as permission
    MERGE (e:ChromeExtensionPermission{id: permission})
    ON CREATE SET
    e.firstseen = timestamp()
    SET
    e.name = permission,
    e.lastupdated = {UpdateTag}
    """

    extensions_permissions_cypher = """
    UNWIND {ExtensionPermissions} as extension_permission
    MATCH (perm:ChromeExtensionPermission{id: extension_permission.permission}),
    (ext:ChromeExtension{id:extension_permission.id})
    MERGE (ext)-[r:DECLARES]->(perm)
    ON CREATE SET
    r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    logger.info(f'CRXcavator ingest - Ingesting {len(extensions)} extensions')
    session.run(extensions_ingestion_cypher, ExtensionsData=extensions, UpdateTag=update_tag)

    logger.info(f'CRXcavator ingest - Ingesting {len(permissions)} Chrome extension permissions')
    session.run(permissions_ingestion_cypher, Permissions=permissions, UpdateTag=update_tag)

    logger.info(f'CRXcavator ingest - Ingesting {len(extension_permissions)} extension to permission links')
    session.run(extensions_permissions_cypher, ExtensionPermissions=extension_permissions, UpdateTag=update_tag)


def transform_user_extensions(user_extension_json):
    """
    Transforms the raw extensions JSON from the API into a list of extensions mapped to users
    :param user_extension_json:  The JSON text blob returned from the CRXcavator API
    :return: Tuple containing unique users list, unique extension list, and extension mapping for ingestion
    """
    user_extensions = user_extension_json.items()
    users_set = set()
    extensions = []
    extensions_by_user = []
    for extension in user_extensions:
        for details in extension[1].items():
            extension_id = extension[0]
            version = details[0]
            extensions.append({
                'extension_id': extension_id,
                'version': version,
                'name': details[1]['name'],
            })
            for user in details[1]['users']:
                users_set.add(user)
                extensions_by_user.append({
                    'id': f"{extension_id}|{version}",
                    'user': user,
                })
    if len(users_set) == 0:
        raise ValueError('No users returned from CRXcavator')
    if len(extensions) == 0:
        raise ValueError('No extensions information returned from CRXcavator')
    if len(extensions_by_user) == 0:
        raise ValueError('No user->extension mapping returned from CRXcavator')

    return list(users_set), extensions, extensions_by_user


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
    MERGE (user:GSuiteUser{email: user_email})
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

    logger.info(f'CRXcavator ingest - Ingesting {len(users)} users')
    session.run(user_ingestion_cypher, Users=users, UpdateTag=update_tag)
    logger.info(f'CRXcavator ingest - Ingesting {len(extensions_by_user)} user->extension relationships')
    session.run(extension_ingestion_cypher, ExtensionsUsers=extensions_by_user, UpdateTag=update_tag)


def sync_extensions(neo4j_session, common_job_parameters, crxcavator_api_key, crxcavator_base_url):
    """
    Performs the sequential tasks to collect, transform, and sync extension data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: None
    """

    user_extensions_json = get_users_extensions(crxcavator_api_key, crxcavator_base_url)
    users, extensions_list, user_extensions = transform_user_extensions(user_extensions_json)
    extension_details = get_extensions(crxcavator_api_key, crxcavator_base_url, extensions_list)
    extensions, permissions_list, extension_permissions = transform_extensions(extension_details)
    load_extensions(
        extensions, permissions_list, extension_permissions,
        neo4j_session, common_job_parameters['UPDATE_TAG'],
    )
    load_user_extensions(users, user_extensions, neo4j_session, common_job_parameters['UPDATE_TAG'])

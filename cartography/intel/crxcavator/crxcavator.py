import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
import requests.auth
from requests import exceptions

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def get_extension_details(
    crxcavator_api_key: str, crxcavator_base_url: str, extension_id: str,
    version: str,
) -> List[Dict]:
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


@timeit
def get_users_extensions(crxcavator_api_key: str, crxcavator_base_url: str) -> List[Dict]:
    """
    Gets listing of all users who have installed each extension
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: JSON text blob containing user email to extension id mapping defined at
    https://crxcavator.io/apidocs#tag/group/paths/~1group~1users~1extensions/get
    """
    return call_crxcavator_api("/group/users/extensions", crxcavator_api_key, crxcavator_base_url)


@timeit
def call_crxcavator_api(api_and_parameters: str, crxcavator_api_key: str, crxcavator_base_url: str) -> List[Dict]:
    """
    Perform the call requested to the CRXcavator API
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :param api_and_parameters: Query string for the API including the required parameters
    :return: Returns JSON text blob for the API called. API spec is at https://crxcavator.io/apidocs
    """
    uri = crxcavator_base_url + api_and_parameters
    try:
        data = requests.get(
            uri,
            headers={
                'Accept': 'application/json',
                'API-Key': crxcavator_api_key,
            },
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout as e:
        # Add context and re-raise for callers to handle
        logger.warning(f"requests.get('{uri}') timed out", e)
        raise
    # if call failed, use requests library to raise an exception
    data.raise_for_status()
    return data.json()


@timeit
def get_extensions(crxcavator_api_key: str, crxcavator_base_url: str, extensions_list: List[Dict]) -> List[Dict]:
    """
    Retrieves the detailed information for all the extension_id and version pairs
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :param extensions_list: list of dictonary items containing the extension_id and version pairs
    :return: list containing all metadata for extensions
    """
    extensions_details: List[Dict] = []
    for extension in extensions_list:
        extension_id = extension['extension_id']
        version = extension['version']
        name = extension['name']
        try:
            details = get_extension_details(crxcavator_api_key, crxcavator_base_url, extension_id, version)
            if not details:
                # we only have the name and version from group API, create minimal version
                logger.debug(f"No results returned from report API for extension {extension_id} {version}")
                details = {
                    'data': dict(
                        webstore={
                            'name': name,
                        },
                    ), 'extension_id': extension_id, 'version': version,
                }
            extensions_details.append(details)
        except exceptions.RequestException as e:
            logger.info(f"API error retrieving details for extension {extension_id}", e)
        except requests.exceptions.Timeout:
            logger.info(f"Skipping {extension_id} due to timeout; continuing")
            continue
    return extensions_details


@timeit
def transform_extensions(extension_details: List[Dict]) -> List[Dict]:
    """
    Transforms the raw extensions JSON from the API into a list of extensions data
    :param extension_details:  List containing the extension details
    :return: List containing extension info for ingestion
    """
    # the JSON returned from the CRXcavator API does not return well formatted objects
    # instead, each object is named after it's key, making enumeration more difficult
    # will build a cleaner object for import into graph

    extensions: List[Dict] = []
    for extension in extension_details:
        extension_id = extension['extension_id']
        version = extension['version']
        data = extension.get('data')
        if not data:
            logger.warning(f'Could not retrieve details for extension {extension}')
            continue
        risk = data.get('risk', {})
        webstore = data.get('webstore', {})
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
    return extensions


@timeit
def get_risk_data(data_dict: Dict, key: str) -> int:
    """
    Gets the total risk value from the provided key and returns the value else 0
    :param data_dict: input data dictionary to parse
    :param key: key name to retrieve
    :return:
    """
    data = data_dict.get(key)
    data_score = data.get('total', 0) if data else 0
    return data_score


@timeit
def load_extensions(extensions: List[Dict], neo4j_session: neo4j.Session, update_tag: int) -> None:
    """
    Ingests the extension details into Neo4J
    :param extensions: List of extension data to load to Neo4J
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """
    ingestion_cypher = """
    UNWIND $ExtensionsData as extension
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
    e.lastupdated = $UpdateTag
    """

    logger.info(f'Ingesting {len(extensions)} extensions')
    neo4j_session.run(ingestion_cypher, ExtensionsData=extensions, UpdateTag=update_tag)


@timeit
def transform_user_extensions(user_extension_json: Dict) -> Tuple[List[Any], List[Dict], List[Dict]]:
    """
    Transforms the raw extensions JSON from the API into a list of extensions mapped to users
    :param user_extension_json:  The JSON text blob returned from the CRXcavator API
    :return: Tuple containing unique users list, unique extension list, and extension mapping for ingestion
    """
    user_extensions = user_extension_json.items()
    users_set = set()
    extensions: List[Dict] = []
    extensions_by_user: List[Dict] = []
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
                if user is None:
                    logger.info(f'bad user for {extension_id}{version}')
                    continue
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


@timeit
def load_user_extensions(
    users: List[Dict], extensions_by_user: Dict, neo4j_session: neo4j.Session,
    update_tag: int,
) -> None:
    """
    Ingests the extension to user mapping details into Neo4J
    :param users: List of user objects to create for mapping
    :param extensions_by_user: List of user to extension id mappings
    :param session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :return: None
    """

    user_ingestion_cypher = """
    UNWIND $Users as user_email
    MERGE (user:GSuiteUser{email: user_email})
    ON CREATE SET
    user.firstseen = timestamp()
    SET user.lastupdated = $UpdateTag
    """

    extension_ingestion_cypher = """
    UNWIND $ExtensionsUsers as extension_user
    MATCH (user:GSuiteUser{email: extension_user.user}),(ext:ChromeExtension{id:extension_user.id})
    MERGE (user)-[r:INSTALLS]->(ext)
    ON CREATE SET
    r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    logger.info(f'Ingesting {len(users)} users')
    neo4j_session.run(user_ingestion_cypher, Users=users, UpdateTag=update_tag)
    logger.info(f'Ingesting {len(extensions_by_user)} user->extension relationships')
    neo4j_session.run(extension_ingestion_cypher, ExtensionsUsers=extensions_by_user, UpdateTag=update_tag)


@timeit
def sync_extensions(
    neo4j_session: neo4j.Session, common_job_parameters: Dict, crxcavator_api_key: str,
    crxcavator_base_url: str,
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync extension data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param crxcavator_api_key: The API key to access the CRXcavator service
    :param crxcavator_base_url: The URL for the CRXcavator API
    :return: None
    """

    try:
        user_extensions_json = get_users_extensions(crxcavator_api_key, crxcavator_base_url)
    except requests.exceptions.Timeout:
        logger.warning("get_users_extensions() failed due to timeout. Skipping CRXcavator sync.")
        return
    users, extensions_list, user_extensions = transform_user_extensions(user_extensions_json)
    extension_details = get_extensions(crxcavator_api_key, crxcavator_base_url, extensions_list)
    extensions = transform_extensions(extension_details)
    load_extensions(extensions, neo4j_session, common_job_parameters['UPDATE_TAG'])
    load_user_extensions(users, user_extensions, neo4j_session, common_job_parameters['UPDATE_TAG'])

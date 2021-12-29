import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_kms_locations(kms: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of kms locations for a given project.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Locations
    """
    try:
        locations = []
        request = kms.projects().locations().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('locations', []):
                for location in response['locations']:
                    location['id'] = location['locationId']
                    locations.append(location)
            request = kms.projects().locations().list_next(previous_request=request, previous_response=response)
        return locations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS locations on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_kms_keyrings(kms: Resource, kms_locations: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of kms keyrings for a given project and locations.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type kms_locations: List
        :param kms_locations: List of kms locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Keyrings in Locations
    """
    try:
        key_rings = []
        for loc in kms_locations:
            request = kms.projects().locations().keyrings().list(parent=f"{loc['name']}")
            while request is not None:
                response = request.execute()
                if response.get('keyRings', []):
                    for key_ring in response['keyRings']:
                        key_ring['loc_id'] = loc['id']
                        key_ring['id'] = key_ring['name']
                        key_rings.append(key_ring)
                request = kms.projects().locations().keyrings().list_next(
                    previous_request=request,
                    previous_response=response,
                )
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS keyrings in locations on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise
    return key_rings


@timeit
def get_kms_crypto_keys(kms: Resource, key_rings: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of kms cryptokeys for a given keyrings and locations.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type key_rings: List
        :param key_rings: List of kms key rings

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Cryptokeys for Keyrings and Locations
    """
    try:
        crypto_keys = []
        for key_ring in key_rings:
            request = kms.projects().locations().keyrings().cryptokeys().list(parent=f"{key_ring['name']}")
            while request is not None:
                response = request.execute()
                if response.get('cryptoKeys', []):
                    for crypto_key in response['cryptoKeys']:
                        crypto_key['keyring_id'] = key_ring['id']
                        crypto_key['id'] = crypto_key['name']
                        crypto_keys.append(crypto_key)
                request = kms.projects().locations().keyrings().cryptokeys().list_next(
                    previous_request=request,
                    previous_response=response,
                )
        return crypto_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS cryptokeys for keyrings in locations on project %s \
                        due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


def load_kms_locations(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_kms_locations_tx, data_list, project_id, update_tag)


def _load_kms_locations_tx(
    tx: neo4j.Transaction, locations: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type locations_resp: List
        :param locations_resp: A list GCP KMS Locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_kms_locations = """
    UNWIND{locations} as loc
    MERGE (location:GCPLocation{id:loc.id})
    ON CREATE SET
        location.firstseen = timestamp()
    SET
        location.name = loc.name,
        location.locationId = loc.locationId,
        location.displayName = loc.displayName,
        location.lastupdated = {gcp_update_tag}
    WITH location, loc
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(location)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_kms_locations,
        locations=locations,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


def load_kms_key_rings(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_kms_key_rings_tx, data_list, project_id, update_tag)


def _load_kms_key_rings_tx(
    tx: neo4j.Transaction, key_rings: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type key_rings_resp: List
        :param key_rings_resp: A list GCP KMS Keyrings for locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_kms_key_rings = """
    UNWIND{key_rings} as keyr
    MERGE (keyring:GCPKMSKeyRing{id:keyr.id})
    ON CREATE SET
        keyring.firstseen = timestamp()
    SET
        keyring.name = keyr.name,
        keyring.createTime = keyr.createTime,
        keyring.lastupdated = {gcp_update_tag}
    WITH keyring, keyr
    MATCH (location:GCPLocation{id:keyr.loc_id})
    MERGE (location)-[r:RESOURCE]->(keyring)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_kms_key_rings,
        key_rings=key_rings,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_kms_crypto_keys(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_kms_crypto_keys_tx, data_list, project_id, update_tag)


@timeit
def _load_kms_crypto_keys_tx(
    tx: neo4j.Transaction, crypto_keys: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type crypto_keys_resp: List
        :param crypt_keys_resp: A list GCP KMS CryptoKeys for keyrings in locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_crypto_keys = """
    UNWIND{crypto_keys} as ck
    MERGE (crypto_key:GCPKMSCryptoKey{id:ck.id})
    ON CREATE SET
        crypto_key.firstseen = timestamp()
    SET
        crypto_key.name = ck.name,
        crypto_key.purpose = ck.purpose,
        crypto_key.createTime = ck.createTime,
        crypto_key.nextRotationTime = ck.nextRotationTime,
        crypto_key.rotationPeriod = ck.rotationPeriod,
        crypto_key.lastupdated = {gcp_update_tag}
    WITH crypto_key, ck
    MATCH (key_ring:GCPKMSKeyRing{id:ck.keyring_id})
    MERGE (key_ring)-[r:RESOURCE]->(crypto_key)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_crypto_keys,
        crypto_keys=crypto_keys,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_kms(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP KMS and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_kms_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_kms(
    neo4j_session: neo4j.Session, kms: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP Cloud KMS using the Cloud KMS resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type kms: The GCP Cloud KMS resource object created by googleapiclient.discovery.build()
    :param kms: The GCP Cloud KMS resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing GCP Cloud KMS for project %s.", project_id)
    # KMS LOCATIONS
    locations = get_kms_locations(kms, project_id)
    load_kms_locations(neo4j_session, locations, project_id, gcp_update_tag)
    # KMS KEYRINGS
    key_rings = get_kms_keyrings(kms, locations, project_id)
    load_kms_key_rings(neo4j_session, key_rings, project_id, gcp_update_tag)
    # KMS CRYPTOKEYS
    crypto_keys = get_kms_crypto_keys(kms, key_rings, project_id)
    load_kms_crypto_keys(neo4j_session, crypto_keys, project_id, gcp_update_tag)
    cleanup_gcp_kms(neo4j_session, common_job_parameters)

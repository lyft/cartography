import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from . import label
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_firestore_databases(firestore: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of firestore databases for a given project.

        :type firestore: Resource
        :param firestore: The firestore resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Firestore Databases
    """
    try:
        firestore_databases = []
        request = firestore.projects().databases().list(parent=f"projects/{project_id}")
        response = request.execute()
        if response.get('databases', []):
            for database in response['databases']:
                database['id'] = database['name']
                firestore_databases.append(database)
        return firestore_databases
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Firestore Databases on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []

        elif err.get('status', '') == 'NOT_FOUND' or err.get('code', '') == 404:
            logger.warning(
                (
                    "Could not retrieve Firestore Databases due to customer has not enabled Firestore for Project %s \
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_firestore_indexes(firestore: Resource, firestore_databases: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of firestore indexes for a given project.

        :type firestore: Resource
        :param firestore: The firestore resource created by googleapiclient.discovery.build()

        :type firestore_databases: list
        :param firestore_database: A list of firestore databases

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Firestore Indexes
    """
    firestore_indexes = []
    for database in firestore_databases:
        try:
            request = firestore.projects().databases().collectionGroups().indexes().list(
                parent=f"{database['name']}/collectionGroups/*",
            )
            while request is not None:
                response = request.execute()
                if response.get('indexes', []):
                    for index in response['indexes']:
                        index['database_id'] = database['id']
                        index['id'] = index['name']
                        index['region'] = database.get('locationId', 'global')
                        firestore_indexes.append(index)
                request = firestore.projects().databases().collectionGroups().indexes().list_next(
                    previous_request=request, previous_response=response,
                )
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Firestore Indexes on project %s due to permissions issues.\
                             Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                return []
            else:
                logger.error(e)
                # raise
                return []
    return firestore_indexes


@timeit
def load_firestore_databases(
    session: neo4j.Session, data_list: List[Dict],
    project_id: str, update_tag: int,
) -> None:
    session.write_transaction(_load_firestore_databases_tx, data_list, project_id, update_tag)


@timeit
def _load_firestore_databases_tx(
    tx: neo4j.Transaction, firestore_databases: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type firestore_databases_resp: List
        :param firestore_databases_resp: A list of Firestore Databases

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_firestore_databases = """
    UNWIND {firestore_databases} as database
    MERGE (d:GCPFirestoreDatabase{id:database.id})
    ON CREATE SET
        d.firstseen = timestamp()
    SET
        d.name = database.name,
        d.locationId = database.locationId,
        d.type = database.type,
        d.region = database.locationId,
        d.concurrencyMode = database.concurrencyMode,
        d.lastupdated = {gcp_update_tag}
    WITH d
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_firestore_databases,
        firestore_databases=firestore_databases,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_firestore_indexes(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_firestore_indexes_tx, data_list, project_id, update_tag)


@timeit
def _load_firestore_indexes_tx(
    tx: neo4j.Transaction, firestore_indexes: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type firestore_indexes_resp: List
        :param firestore_indexes_resp: A list of Firestore Databases

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_firestore_indexes = """
    UNWIND {firestore_indexes} as index
    MERGE (ix:GCPFirestoreIndex{id:index.id})
    ON CREATE SET
        ix.firstseen = timestamp()
    SET
        ix.name = index.name,
        ix.queryScope = index.queryScope,
        ix.region = index.region,
        ix.state = index.state,
        ix.lastupdated = {gcp_update_tag}
    WITH ix,index
    MATCH (d:GCPFirestoreDatabase{id:index.database_id})
    MERGE (d)-[r:HAS_INDEX]->(ix)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_firestore_indexes,
        firestore_indexes=firestore_indexes,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_firestore(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
        Delete out-of-date GCP Firestore Databases, Indexes and relationships

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    run_cleanup_job('gcp_firestore_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, firestore: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
        Get GCP Cloud Firestore using the Cloud Firestore resource object, ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type firestore: The GCP Firestore resource object created by googleapiclient.discovery.build()
        :param firestore: The GCP Firestore resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    logger.info("Syncing GCP Cloud Firestore for project %s.", project_id)
    # FIRESTORE DATABASES
    firestore_databases = get_firestore_databases(firestore, project_id)
    load_firestore_databases(neo4j_session, firestore_databases, project_id, gcp_update_tag)
    label.sync_labels(neo4j_session, firestore_databases, gcp_update_tag, common_job_parameters)
    # FIRESTORE INDEXES
    firestore_indexes = get_firestore_indexes(firestore, firestore_databases, project_id)
    load_firestore_indexes(neo4j_session, firestore_indexes, project_id, gcp_update_tag)
    cleanup_firestore(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, firestore_indexes, gcp_update_tag, common_job_parameters)

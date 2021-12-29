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
def get_sql_instances(sql: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of sql instances for a given project.

        :type sql: Resource
        :param sql: The sql resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Sql Instances
    """
    try:
        sql_instances = []
        request = sql.instances().list(project=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('items', []):
                for item in response['items']:
                    item['id'] = f"project/{project_id}/instances/{item['name']}"
                    sql_instances.append(item)
            request = sql.instances().list_next(previous_request=request, previous_response=response)
        return sql_instances
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Sql Instances on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_sql_users(sql: Resource, sql_instances: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of sql instance users for a given project.

        :type sql: Resource
        :param sql: The sql resource created by googleapiclient.discovery.build()

        :type sql_instances: List
        :type sql_instances: List of sql instances

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Sql Instance Users
    """
    for inst in sql_instances:
        try:
            sql_users = []
            request = sql.users().list(project=f"projects/{project_id}", instance=f"{inst['name']}")
            while request is not None:
                response = request.execute()
                if response.get('items', []):
                    for item in response['items']:
                        item['instance_id'] = inst['id']
                        item['id'] = f"project/{project_id}/instances/{inst['name']}/users/{item['name']}"
                        sql_users.append(item)
                    while 'nextPageToken' in response:
                        response = sql.users().list(
                            project=f"projects/{project_id}",
                            instance=f"{inst['name']}", pageToken=response['nextPageToken'],
                        )
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Sql Instance Users on project %s due to permissions issues.\
                             Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                return []
            else:
                raise
    return sql_users


@timeit
def load_sql_instances(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_sql_instances_tx, data_list, project_id, update_tag)


@timeit
def _load_sql_instances_tx(tx: neo4j.Transaction, instances: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type instances_resp: List
        :param instances_resp: A list of SQL Instances

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_sql_instances = """
    UNWIND {instances} as instance
    MERGE (i:GCPSQLInstance{id:instance.id})
    ON CREATE SET
        i.firstseen = timestamp()
    SET
        i.state = instance.state,
        i.databaseVersion = instance.databaseVersion,
        i.masterInstanceName = instance.MasterInstanceName,
        i.maxDiskSize = instance.maxDiskSize,
        i.currentDiskSize = instance.currentDiskSize,
        i.instanceType = instance.instanceType,
        i.connectionName = instance.connectionName,
        i.name = instance.name,
        i.region = instance.region,
        i.gceZone = instance.gceZone,
        i.secondaryGceZone = instance.secondaryGceZone,
        i.satisfiesPzs = instance.satisfiesPzs,
        i.createTime = instance.createTime,
        i.lastupdated = {gcp_update_tag}
    WITH i
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_sql_instances,
        instances=instances,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_sql_users(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_sql_users_tx, data_list, project_id, update_tag)


@timeit
def _load_sql_users_tx(tx: neo4j.Transaction, sql_users: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type sql_users_resp: List
        :param sql_users_resp: A list of SQL Users

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_sql_users = """
    UNWIND {sql_users} as user
    MERGE (u:GCPSQLUser{id:user.id})
    ON CREATE SET
        u.firstseen = timestamp()
    SET
        u.name = user.name,
        u.host = user.host,
        u.instance = user.instance,
        u.project = user.project,
        u.type = user.type,
        u.lastupdated = {gcp_update_tag}
    WITH u,user
    MATCH (i:GCPSQLInstance{id:user.instance_id})
    MERGE (i)-[r:USED_BY]->(u)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_sql_users,
        sql_users=sql_users,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_sql(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
        Delete out-of-date GCP SQL Instances and relationships

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    run_cleanup_job('gcp_sql_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_sql(
    neo4j_session: neo4j.Session, sql: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
        Get GCP Cloud SQL Instances and Users using the Cloud SQL resource object,
        ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type sql: The GCP Cloud SQL resource object created by googleapiclient.discovery.build()
        :param sql: The GCP Cloud SQL resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    logger.info("Syncing GCP Cloud SQL for project %s.", project_id)
    # SQL INSTANCES
    sqlinstances = get_sql_instances(sql, project_id)
    load_sql_instances(neo4j_session, sqlinstances, project_id, gcp_update_tag)
    # SQL USERS
    users = get_sql_users(sql, project_id, sqlinstances)
    load_sql_users(neo4j_session, users, project_id, gcp_update_tag)
    cleanup_sql(neo4j_session, common_job_parameters)

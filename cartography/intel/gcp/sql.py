import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_sql_instances(sql: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
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
        request = sql.instances().list(project=project_id)
        while request is not None:
            response = request.execute()
            if response.get('items', []):
                for item in response['items']:
                    item['id'] = f"projects/{project_id}/instances/{item['name']}"
                    item['ipV4Enabled'] = item.get('settings', {}).get('ipConfiguration', {}).get('ipV4Enabled', False)
                    item['consolelink'] = gcp_console_link.get_console_link(
                        resource_name='sql_instance', project_id=project_id, sql_instance_name=item['name'],
                    )
                    if regions is None:
                        sql_instances.append(item)
                    else:
                        if item.get('region') in regions:
                            sql_instances.append(item)
            request = sql.instances().list_next(previous_request=request, previous_response=response)
        if common_job_parameters.get('pagination', {}).get('sql', None):
            pageNo = common_job_parameters.get("pagination", {}).get("sql", None)["pageNo"]
            pageSize = common_job_parameters.get("pagination", {}).get("sql", None)["pageSize"]
            totalPages = len(sql_instances) / pageSize
            if int(totalPages) != totalPages:
                totalPages = totalPages + 1
            totalPages = int(totalPages)
            if pageNo < totalPages or pageNo == totalPages:
                logger.info(f'pages process for sql instances {pageNo}/{totalPages} pageSize is {pageSize}')
            page_start = (
                common_job_parameters.get('pagination', {}).get('sql', None)[
                    'pageNo'
                ] - 1
            ) * common_job_parameters.get('pagination', {}).get('sql', None)['pageSize']
            page_end = page_start + common_job_parameters.get('pagination', {}).get('sql', None)['pageSize']
            if page_end > len(sql_instances) or page_end == len(sql_instances):
                sql_instances = sql_instances[page_start:]
            else:
                has_next_page = True
                sql_instances = sql_instances[page_start:page_end]
                common_job_parameters['pagination']['sql']['hasNextPage'] = has_next_page
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
    sql_users = []
    for inst in sql_instances:
        try:
            request = sql.users().list(project=project_id, instance=f"{inst['name']}")
            while request is not None:
                response = request.execute()
                if response.get('items', []):
                    for item in response['items']:
                        item['instance_id'] = inst['id']
                        item['id'] = f"projects/{project_id}/instances/{inst['name']}/users/{item['name']}"
                        item['consolelink'] = gcp_console_link.get_console_link(
                            project_id=project_id, resource_name='sql_user', sql_instance_name=inst['name'],
                        )
                        sql_users.append(item)
                if 'nextPageToken' in response:
                    request = sql.users().list(
                        project=f"projects/{project_id}",
                        instance=f"{inst['name']}", pageToken=response['nextPageToken'],
                    )
                else:
                    request = None
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Sql Instance Users on project %s due to permissions issues.\
                            Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                continue
                # return []
            else:
                # raise
                # return []
                continue

    return sql_users


@timeit
def get_sql_databases(sql: Resource, instance: Dict, project_id: str) -> List[Dict]:
    """
        Returns a list of sql database for a given project.

        :type sql: Resource
        :param sql: The sql resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Sql Database
    """
    sql_database = []
    try:
        request = sql.databases().list(project=project_id, instance=f"{instance['name']}")

        response = request.execute()

        if response.get('items', []):
            # logger.info(f"Time to process CloudSQL======= ", response)
            for item in response['items']:
                item['state'] = instance['state']
                item['region'] = instance['region']
                item['instance_id'] = instance['id']
                item['id'] = f"projects/{project_id}/instances/{instance['name']}/databases/{item['name']}"
                item['consolelink'] = gcp_console_link.get_console_link(
                    project_id=project_id, resource_name='sql_instance', sql_instance_name=instance['name'],
                )
                sql_database.append(item)

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Sql Instance database on project %s due to permissions issues.\
                        Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )

    return sql_database


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
    UNWIND $instances as instance
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
        i.ipV4Enabled = instance.ipV4Enabled,
        i.region = instance.region,
        i.gceZone = instance.gceZone,
        i.secondaryGceZone = instance.secondaryGceZone,
        i.satisfiesPzs = instance.satisfiesPzs,
        i.createTime = instance.createTime,
        i.consolelink = instance.consolelink,
        i.lastupdated = $gcp_update_tag
    WITH i
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
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
    UNWIND $sql_users as user
    MERGE (u:GCPSQLUser{id:user.id})
    ON CREATE SET
        u.firstseen = timestamp()
    SET
        u.name = user.name,
        u.host = user.host,
        u.instance = user.instance,
        u.region = $region,
        u.project = user.project,
        u.type = user.type,
        u.consolelink = user.consolelink,
        u.lastupdated = $gcp_update_tag
    WITH u,user
    MATCH (i:GCPSQLInstance{id:user.instance_id})
    MERGE (i)-[r:USED_BY]->(u)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_sql_users,
        sql_users=sql_users,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_sql_databases(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_sql_databases_tx, data_list, project_id, update_tag)


@timeit
def _load_sql_databases_tx(tx: neo4j.Transaction, sql_databases: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type sql_databases: List
        :param sql_databases: A list of SQL database

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_sql_databases = """
    UNWIND $sql_databases as database
    MERGE (d:GCPSQLDatabase{id:database.id})
    ON CREATE SET
        d.firstseen = timestamp()
    SET
        d.name = database.name,
        d.charset = database.charset,
        d.instance = database.instance,
        d.collation=database.collation,
        d.state = database.state,
        d.compatibilitylevel=database.sqlserverDatabaseDetails.compatibilityLevel,
        d.recoverymodel=database.sqlserverDatabaseDetails.recoveryModel,
        d.region = database.region,
        d.project = database.project,
        d.consolelink = database.consolelink,
        d.lastupdated = $gcp_update_tag
    WITH d,database
    MATCH (i:GCPSQLInstance{id:database.instance_id})
    MERGE (i)-[r:HAS_DATABASE]->(d)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_sql_databases,
        sql_databases=sql_databases,
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
def sync(
    neo4j_session: neo4j.Session, sql: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
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
    tic = time.perf_counter()

    logger.info("Syncing CloudSQL for project '%s', at %s.", project_id, tic)

    # SQL INSTANCES
    sqlinstances = get_sql_instances(sql, project_id, regions, common_job_parameters)
    load_sql_instances(neo4j_session, sqlinstances, project_id, gcp_update_tag)
    logger.info("Load GCP Cloud SQL Instances completed for project %s.", project_id)
    label.sync_labels(
        neo4j_session, sqlinstances, gcp_update_tag,
        common_job_parameters, 'sql instances', 'GCPSQLInstance',
    )

    logger.info("Syncing GCP Cloud SQL Users for project %s.", project_id)
    # SQL USERS
    users = get_sql_users(sql, sqlinstances, project_id)
    load_sql_users(neo4j_session, users, project_id, gcp_update_tag)
    for instance in sqlinstances:
        database = get_sql_databases(sql, instance, project_id)
        load_sql_databases(neo4j_session, database, project_id, gcp_update_tag)

    cleanup_sql(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process CloudSQL: {toc - tic:0.4f} seconds")

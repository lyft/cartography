import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_resource_groups(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_resource_groups_tx, subscription_id, data_list, update_tag)


def load_tags(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tags_tx, data_list, update_tag)


@timeit
def get_resource_management_client(credentials: Credentials, subscription_id: str) -> ResourceManagementClient:
    client = ResourceManagementClient(credentials, subscription_id)
    return client


@timeit
def get_resource_groups_list(client: ResourceManagementClient) -> List[Dict]:
    try:
        resource_groups_list = list(map(lambda x: x.as_dict(), client.resource_groups.list()))

        return resource_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving resource groups - {e}")
        return []


def _load_resource_groups_tx(
    tx: neo4j.Transaction, subscription_id: str, resource_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_group = """
    UNWIND {resource_groups_list} AS group
    MERGE (t:AzureResourceGroup{id: group.id})
    ON CREATE SET t.firstseen = timestamp(),
    t.type = group.type,
    t.location = group.location,
    t.managedBy = group.managedBy
    SET t.lastupdated = {update_tag},
    t.name = group.name
    WITH t
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_group,
        resource_groups_list=resource_groups_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_resource_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_resource_groups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_tags_list(
    neo4j_session: neo4j.Session, client: ResourceManagementClient, resource_groups_list: List[Dict],
) -> List[Dict]:
    try:
        tags_list: List[Dict] = []
        for resource_group in resource_groups_list:
            if "tags" in resource_group.keys() and len(resource_group['tags']) != 0:
                for tagname in resource_group['tags']:
                    tags_list = tags_list + [{
                        'id': resource_group['id'] + "/providers/Microsoft.Resources/tags/" + tagname,
                        'name': tagname, 'value': resource_group['tags']
                        [tagname], 'type': 'Microsoft.Resources/tags', 'resource_id': resource_group['id'],
                        'resource_group': resource_group['name'],
                    }]
            for resource in client.resources.list_by_resource_group(resource_group_name=resource_group['name']):
                if neo4j_session.run("MATCH (n) WHERE n.id={id} return count(*)", id=resource.id).single().value() == 1:
                    if resource.tags:
                        for tagname in resource.tags:
                            tags_list = tags_list + \
                                [{
                                    'id': resource.id + "/providers/Microsoft.Resources/tags/" + tagname,
                                    'name': tagname, 'value': resource.tags[tagname],
                                    'type': 'Microsoft.Resources/tags',
                                    'resource_id': resource.id, 'resource_group': resource_group['name'],
                                }]

        return tags_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tags - {e}")
        return []


def _load_tags_tx(tx: neo4j.Transaction, tags_list: List[Dict], update_tag: int) -> None:
    ingest_tag = """
    UNWIND {tags_list} AS tag
    MERGE (t:AzureTag{id: tag.id})
    ON CREATE SET t.firstseen = timestamp(),
    t.type = tag.type,
    t.resource_group = tag.resource_group
    SET t.lastupdated = {update_tag},
    t.value = tag.value,
    t.name = tag.name
    WITH t,tag
    MATCH (l) where l.id = tag.resource_id
    MERGE (l)-[r:TAGGED]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_tag,
        tags_list=tags_list,
        update_tag=update_tag,
    )


def cleanup_tags(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tags_cleanup.json', neo4j_session, common_job_parameters)


def sync_tags(
    neo4j_session: neo4j.Session, client: ResourceManagementClient, resource_groups_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    tags_list = get_tags_list(neo4j_session, client, resource_groups_list)
    load_tags(neo4j_session, tags_list, update_tag)
    cleanup_tags(neo4j_session, common_job_parameters)


def sync_resource_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_resource_management_client(credentials, subscription_id)
    resource_groups_list = get_resource_groups_list(client)
    load_resource_groups(neo4j_session, subscription_id, resource_groups_list, update_tag)
    cleanup_resource_groups(neo4j_session, common_job_parameters)
    sync_tags(neo4j_session, client, resource_groups_list, update_tag, common_job_parameters)


@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing tags for subscription '%s'.", subscription_id)

    sync_resource_groups(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)

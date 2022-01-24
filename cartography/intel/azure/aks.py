import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerservice import ContainerServiceClient

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_aks(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_aks_tx, subscription_id, data_list, update_tag)


def load_container_registries(
    session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int,
) -> None:
    session.write_transaction(_load_container_registries_tx, subscription_id, data_list, update_tag)


def load_container_registry_replications(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_container_registry_replications_tx, data_list, update_tag)


def load_container_registry_runs(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_container_registry_runs_tx, data_list, update_tag)


def load_container_registry_tasks(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_container_registry_tasks_tx, data_list, update_tag)


def load_container_registry_webhooks(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_container_registry_webhooks_tx, data_list, update_tag)


def load_container_groups(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_container_groups_tx, subscription_id, data_list, update_tag)


def load_containers(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_containers_tx, data_list, update_tag)


@ timeit
def get_client(credentials: Credentials, subscription_id: str) -> ContainerServiceClient:
    client = ContainerServiceClient(credentials, subscription_id)
    return client


@ timeit
def get_container_registry_Client(credentials: Credentials, subscription_id: str) -> ContainerRegistryManagementClient:
    client = ContainerRegistryManagementClient(credentials, subscription_id)
    return client


@ timeit
def get_container_instance_Client(credentials: Credentials, subscription_id: str) -> ContainerInstanceManagementClient:
    client = ContainerInstanceManagementClient(credentials, subscription_id)
    return client


@ timeit
def get_aks_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        aks_list = list(map(lambda x: x.as_dict(), client.managed_clusters.list()))

        for aks in aks_list:
            x = aks['id'].split('/')
            aks['resource_group'] = x[x.index('resourcegroups') + 1]

        return aks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving AKS - {e}")
        return []


def _load_aks_tx(tx: neo4j.Transaction, subscription_id: str, aks_list: List[Dict], update_tag: int) -> None:
    ingest_aks = """
    UNWIND {aks_list} AS aks
    MERGE (a:AzureCluster{id: aks.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = aks.type,
    a.location = aks.location,
    a.resourcegroup = aks.resource_group
    SET a.lastupdated = {update_tag},
    a.name = aks.name
    WITH a
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_aks,
        aks_list=aks_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_aks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_aks_cleanup.json', neo4j_session, common_job_parameters)


def sync_aks(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    aks_list = get_aks_list(credentials, subscription_id)
    load_aks(neo4j_session, subscription_id, aks_list, update_tag)
    cleanup_aks(neo4j_session, common_job_parameters)


@ timeit
def get_container_registries_list(client: ContainerRegistryManagementClient) -> List[Dict]:
    try:
        container_registries_list = list(map(lambda x: x.as_dict(), client.registries.list()))

        for registry in container_registries_list:
            x = registry['id'].split('/')
            registry['resource_group'] = x[x.index('resourcegroups') + 1]

        return container_registries_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving registries - {e}")
        return []


def _load_container_registries_tx(
    tx: neo4j.Transaction, subscription_id: str, container_registries_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_registry = """
    UNWIND {container_registries_list} AS registry
    MERGE (a:AzureContainerRegistry{id: registry.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = registry.type,
    a.location = registry.location,
    a.resourcegroup = registry.resource_group
    SET a.lastupdated = {update_tag},
    a.name = registry.name
    WITH a
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_registry,
        container_registries_list=container_registries_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_container_registries(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_registries_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_registries(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_container_registry_Client(credentials, subscription_id)
    container_registries_list = get_container_registries_list(client)
    load_container_registries(neo4j_session, subscription_id, container_registries_list, update_tag)
    cleanup_container_registries(neo4j_session, common_job_parameters)
    sync_container_registry_replications(
        neo4j_session, client, container_registries_list, update_tag, common_job_parameters,
    )
    sync_container_registry_runs(
        neo4j_session, client, container_registries_list, update_tag, common_job_parameters,
    )
    sync_container_registry_tasks(
        neo4j_session, client, container_registries_list, update_tag, common_job_parameters,
    )
    sync_container_registry_webhooks(
        neo4j_session, client, container_registries_list, update_tag, common_job_parameters,
    )


@ timeit
def get_container_registry_replications_list(
    client: ContainerRegistryManagementClient, container_registries_list: List[Dict],
) -> List[Dict]:
    try:
        container_registry_replications_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_replications_list = container_registry_replications_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.replications.list(
                            registry_name=container_registry['name'],
                            resource_group_name=container_registry['resource_group'],
                        ),
                    ),
                )

        for replication in container_registry_replications_list:
            x = replication['id'].split('/')
            replication['resource_group'] = x[x.index('resourcegroups') + 1]
            replication['container_registry_id'] = replication['id'][:replication['id'].index("/replications")]

        return container_registry_replications_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_replications - {e}")
        return []


def _load_container_registry_replications_tx(
    tx: neo4j.Transaction, container_registry_replications_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_replication = """
    UNWIND {container_registry_replications_list} AS replication
    MERGE (a:AzureContainerRegistryReplication{id: replication.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = replication.type,
    a.location = replication.location,
    a.resourcegroup = replication.resource_group
    SET a.lastupdated = {update_tag},
    a.name = replication.name
    WITH a,replication
    MATCH (owner:AzureContainerRegistry{id: replication.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_replication,
        container_registry_replications_list=container_registry_replications_list,
        update_tag=update_tag,
    )


def cleanup_container_registry_replications(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_registry_replications_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_registry_replications(
    neo4j_session: neo4j.Session, client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_replications_list = get_container_registry_replications_list(client, container_registries_list)
    load_container_registry_replications(neo4j_session, container_registry_replications_list, update_tag)
    cleanup_container_registry_replications(neo4j_session, common_job_parameters)


@ timeit
def get_container_registry_runs_list(
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
) -> List[Dict]:
    try:
        container_registry_runs_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_runs_list = container_registry_runs_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.runs.list(
                            registry_name=container_registry['name'],
                            resource_group_name=container_registry['resource_group'],
                        ),
                    ),
                )

        for run in container_registry_runs_list:
            x = run['id'].split('/')
            run['resource_group'] = x[x.index('resourcegroups') + 1]
            run['container_registry_id'] = run['id'][:run['id'].index("/runs")]

        return container_registry_runs_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_runs - {e}")
        return []


def _load_container_registry_runs_tx(
    tx: neo4j.Transaction, container_registry_runs_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_run = """
    UNWIND {container_registry_runs_list} AS run
    MERGE (a:AzureContainerRegistryRun{id: run.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = run.type,
    a.resourcegroup = run.resource_group
    SET a.lastupdated = {update_tag},
    a.name = run.name
    WITH a,run
    MATCH (owner:AzureContainerRegistry{id: run.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_run,
        container_registry_runs_list=container_registry_runs_list,
        update_tag=update_tag,
    )


def cleanup_container_registry_runs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_registry_runs_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_registry_runs(
    neo4j_session: neo4j.Session, client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_runs_list = get_container_registry_runs_list(client, container_registries_list)
    load_container_registry_runs(neo4j_session, container_registry_runs_list, update_tag)
    cleanup_container_registry_runs(neo4j_session, common_job_parameters)


@ timeit
def get_container_registry_tasks_list(
    client: ContainerRegistryManagementClient, container_registries_list: List[Dict],
) -> List[Dict]:
    try:
        container_registry_tasks_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_tasks_list = container_registry_tasks_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.runs.list(
                            registry_name=container_registry['name'],
                            resource_group_name=container_registry['resource_group'],
                        ),
                    ),
                )

        for task in container_registry_tasks_list:
            x = task['id'].split('/')
            task['resource_group'] = x[x.index('resourcegroups') + 1]
            task['container_registry_id'] = task['id'][:task['id'].index("/tasks")]

        return container_registry_tasks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_tasks - {e}")
        return []


def _load_container_registry_tasks_tx(
    tx: neo4j.Transaction, container_registry_tasks_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_task = """
    UNWIND {container_registry_tasks_list} AS task
    MERGE (a:AzureContainerRegistryTask{id: task.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = task.type,
    a.location=task.location,
    a.resourcegroup = task.resource_group
    SET a.lastupdated = {update_tag},
    a.name = task.name
    WITH a,task
    MATCH (owner:AzureContainerRegistry{id: task.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_task,
        container_registry_tasks_list=container_registry_tasks_list,
        update_tag=update_tag,
    )


def cleanup_container_registry_tasks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_registry_tasks_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_registry_tasks(
    neo4j_session: neo4j.Session, client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_tasks_list = get_container_registry_tasks_list(client, container_registries_list)
    load_container_registry_tasks(neo4j_session, container_registry_tasks_list, update_tag)
    cleanup_container_registry_tasks(neo4j_session, common_job_parameters)


@ timeit
def get_container_registry_webhooks_list(
    client: ContainerRegistryManagementClient, container_registries_list: List[Dict],
) -> List[Dict]:
    try:
        container_registry_webhooks_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_webhooks_list = container_registry_webhooks_list + \
                list(
                    map(
                        lambda x: x.as_dict(), client.webhooks.list(
                            registry_name=container_registry['name'],
                            resource_group_name=container_registry['resource_group'],
                        ),
                    ),
                )

        for webhook in container_registry_webhooks_list:
            x = webhook['id'].split('/')
            webhook['resource_group'] = x[x.index('resourcegroups') + 1]
            webhook['container_registry_id'] = webhook['id'][:webhook['id'].index("/webhooks")]

        return container_registry_webhooks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_webhooks - {e}")
        return []


def _load_container_registry_webhooks_tx(
    tx: neo4j.Transaction, container_registry_webhooks_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_webhook = """
    UNWIND {container_registry_webhooks_list} AS webhook
    MERGE (a:AzureContainerRegistryWebhook{id: webhook.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = webhook.type,
    a.location=webhook.location,
    a.resourcegroup = webhook.resource_group
    SET a.lastupdated = {update_tag},
    a.name = webhook.name
    WITH a,webhook
    MATCH (owner:AzureContainerRegistry{id: webhook.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_webhook,
        container_registry_webhooks_list=container_registry_webhooks_list,
        update_tag=update_tag,
    )


def cleanup_container_registry_webhooks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_registry_webhooks_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_registry_webhooks(
    neo4j_session: neo4j.Session, client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_webhooks_list = get_container_registry_webhooks_list(client, container_registries_list)
    load_container_registry_webhooks(neo4j_session, container_registry_webhooks_list, update_tag)
    cleanup_container_registry_webhooks(neo4j_session, common_job_parameters)


@ timeit
def get_container_groups_list(client: ContainerInstanceManagementClient) -> List[Dict]:
    try:
        container_groups_list = list(map(lambda x: x.as_dict(), client.container_groups.list()))

        for group in container_groups_list:
            x = group['id'].split('/')
            group['resource_group'] = x[x.index('resourcegroups') + 1]

        return container_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving Container Group - {e}")
        return []


def _load_container_groups_tx(
    tx: neo4j.Transaction, subscription_id: str, container_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_container_group = """
    UNWIND {container_groups_list} AS group
    MERGE (a:AzureContainerGroup{id: group.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = group.type,
    a.location = group.location,
    a.resourcegroup = group.resource_group
    SET a.lastupdated = {update_tag},
    a.name = group.name
    WITH a
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container_group,
        container_groups_list=container_groups_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_container_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_container_groups_cleanup.json', neo4j_session, common_job_parameters)


def sync_container_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_container_instance_Client(credentials, subscription_id)
    container_groups_list = get_container_groups_list(client)
    load_container_groups(neo4j_session, subscription_id, container_groups_list, update_tag)
    cleanup_container_groups(neo4j_session, common_job_parameters)
    sync_containers(neo4j_session, container_groups_list, update_tag, common_job_parameters)


@ timeit
def get_containers_list(container_groups_list: List[Dict]) -> List[Dict]:
    try:
        containers_list: List[Dict] = []
        for container_group in container_groups_list:
            container_list = container_group['properties']['containers']
            for container in container_list:
                container["id"] = f"{container_group.get('id',None)}/containers/{container.get('name',None)}"
                container["container_group_id"] = container_group['id']
                container["resource_group"] = container_group["resource_group"]
                container["type"] = "Microsoft.ContainerInstance/containers"
            containers_list = containers_list + container_list

        return containers_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving containers - {e}")
        return []


def _load_containers_tx(tx: neo4j.Transaction, containers_list: List[Dict], update_tag: int) -> None:
    ingest_container = """
    UNWIND {containers_list} AS container
    MERGE (a:AzureContainer{id: container.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = container.type,
    a.name = container.name,
    a.resourcegroup = container.resource_group
    SET a.lastupdated = {update_tag}
    WITH a,container
    MATCH (owner:AzureContainerGroup{id: container.container_group_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_container,
        containers_list=containers_list,
        update_tag=update_tag,
    )


def cleanup_containers(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_containers_cleanup.json', neo4j_session, common_job_parameters)


def sync_containers(
    neo4j_session: neo4j.Session, container_groups_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    containers_list = get_containers_list(container_groups_list)
    load_containers(neo4j_session, containers_list, update_tag)
    cleanup_containers(neo4j_session, common_job_parameters)


@ timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict,


) -> None:
    logger.info("Syncing AKS for subscription '%s'.", subscription_id)

    sync_aks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_container_registries(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)
    sync_container_groups(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters)

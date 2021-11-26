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
def get_project_roles(iam: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of Roles within the given project .

        :type iam: The GCP IAM resource object
        :param iam: The IAM resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Project roles
    """
    try:
        roles = []
        request = iam.projects().roles().list(parent=f'projects/{project_id}')
        while request is not None:
            response = request.execute()
            if response.get('roles', []):
                for role in response['roles']:
                    role['id'] = role['name']
                    roles.append(role)
            request = iam.projects().roles().list_next(previous_request=request, previous_response=response)
        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve roles on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_workloadidentitypools(iam: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of Workload Identity Pools within the given project .

        :type iam: The GCP IAM resource object
        :param iam: The IAM resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Workload Identity Pools
    """
    try:
        pools = []
        request = iam.projects().locations().workloadIdentityPools.list(parent=f'projects/{project_id}/locations/*')
        while request is not None:
            response = request.execute()
            if response.get('workloadIdentityPools', []):
                for pool in response('workloadIdentityPools'):
                    pool['id'] = f"project/{project_id}/worloadIdentityPools/{pool['name']}"
                    pools.append(pool)
            request = iam.projects().locations().workloadIdentityPools.list_next(previous_request=request, previous_response=response)
        return pools
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve workloadIdentityPools on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_workloadidentitypoolproviders(iam: Resource, pools: List[Resource], project_id: str) -> List[Dict]:
    """
        Returns a list of Workload Identity Pools Providers within the given project and workloadidentitypool .

        :type iam: The GCP IAM resource object
        :param iam: The IAM resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Workload Identity Pools Providers
    """
    try:
        providers = []
        for pool in pools:
            request = iam.projects().locations().workloadIdentityPools().providers().list(parent=f"projects/{project_id}/locations/*/worloadIdentityPools/{pool['name']}")
            while request is not None:
                response = request.execute()
                if response.get('workloadIdentityPoolProviders', []):
                    for provider in response['workloadIdentityPoolProviders']:
                        provider['id'] = f"projects/{project_id}/workloadIdentityPools/{pool['name']}/workloadIdentityPoolsProviders/{provider['name']}"
                        provider['pool'] = pool['name']
                        providers.append(provider)
                request = iam.projects().locations().workloadIdentityPools().providers().list_next(previous_request=request, previous_response=response)
            return providers
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve workloadIdentityPools providers on workload identity pools %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_service_accounts(iam: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of service accounts within a project.

        :type iam: The GCP IAM resource object
        :param iam: The IAM resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of service accounts
    """
    try:
        accounts = []
        request = iam.projects().serviceAccounts().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('accounts', []):
                for account in response['accounts']:
                    account['id'] = account['name']
                    accounts.append(account)
            request = iam.projects().serviceAccounts().list_next(previous_request=request, previous_response=response)
        return accounts
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve service accounts on projects %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_iam_roles(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_iam_roles_tx, data_list, project_id, update_tag)


@timeit
def _load_iam_roles_tx(tx: neo4j.Transaction, roles: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type roles_resp: List
        :param roles_resp: A list GCP IAM roles

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_iam_roles = """
    UNWIND{roles} as rl
    MERGE (roles:GCPIAMRole{id:rl.id})
    ON CREATE SET
        role.firstseen = timestamp()
    SET
        role.name = rl.name,
        role.title = rl.title,
        role.stage = rl.stage,
        role.deleted = rl.deleted
    WITH roles,rl
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(role)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_iam_roles,
        roles=roles,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_workloadidentitypools(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_workloadidentitypools_tx, data_list, project_id, update_tag)


@timeit
def _load_workloadidentitypools_tx(tx: neo4j.Transaction, pools: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type pools_resp: List
        :param pools_resp: A list GCP IAM Workload Identity Pools

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_workloadidentitypools = """
    UNWIND{pools} as pl
    MERGE (pool:GCPIAMWorkloadidentitypool{id:pl.id})
    ON CREATE SET
        pool.firstseen = timestamp()
    SET
        pool.name = pl.name,
        pool.displayName = pl.displayName,
        pool.state = pl.state,
        pool.disabled = pl.disabled
    WITH pool,pl
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]-(pool)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_workloadidentitypools,
        pools=pools,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_workloadidentitypools_providers(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_workloadidentitypools_providers_tx, data_list, project_id, update_tag)


@timeit
def _load_workloadidentitypools_providers_tx(tx: neo4j.Transaction, providers: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type providers_resp: List
        :param providers_resp: A list GCP IAM Workload Identity Pool Providers

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_workloadidentitypools_providers = """
    UNWIND{providers} as prov
    MERGE (provider:GCPIAMWorloadidentitypoolprovider{id:prov.id})
    ON CREATE SET
        provider.firstseen = timestamp()
    SET
        provider.name = prov.name,
        provider.displayName = prov.displayName,
        provider.state = prov.state,
        provider.disabled = prov.disabled
    WITH provider, prov
    MATCH (pool:GCPIAMWorkloadidentitypool{id:provider.pool})
    MERGE (pool)-[r:PROVIDES]->(provider)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_workloadidentitypools_providers,
        providers=providers,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_service_accounts(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_service_accounts_tx, data_list, project_id, update_tag)


@timeit
def _load_service_accounts_tx(tx: neo4j.Transaction, accounts: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type accounts_resp: List
        :param accounts_resp: A list GCP IAM Service Accounts

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_service_accounts = """
    UNWIND{accounts} as acc
    MERGE (account:GCPIAMServiceAccount{id:acc.id})
    ON CREATE SET
        account.firstseen = timestamp()
    SET
        account.name = acc.name,
        account.projectID = acc.projectId,
        account.uniqueId = acc.uniqueId,
        account.displayName = acc.displayName,
        account.disabled = acc.disabled
    WITH account,acc
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(account)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_service_accounts,
        accounts=accounts,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_iam(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
        Delete out-of-date GCP IAM resources and relationships

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    run_cleanup_job('gcp_iam_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_iam(
    neo4j_session: neo4j.Session, iam: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
        Get GCP DNS IAM roles, Workload Identity Pools, Workload Identity Pool Providers and Service Accounts using the IAM resource object, ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type iam: The IAM resource object created by googleapiclient.discovery.build()
        :param dns: The GCP IAM resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    logger.info("Syncing IAM resources for project %s.", project_id)
    # IAM roles
    roles = get_project_roles(iam, project_id)
    load_iam_roles(neo4j_session, roles, project_id, gcp_update_tag)
    # IAM Workloadidentitypools
    pools = get_workloadidentitypools(iam, project_id)
    load_workloadidentitypools(neo4j_session, pools, project_id, gcp_update_tag)
    # IAM Workloadidentitypool Providers
    providers = get_workloadidentitypoolproviders(iam, pools, project_id)
    load_workloadidentitypools_providers(neo4j_session, providers, project_id, gcp_update_tag)
    # IAM Service Accounts
    accounts = get_service_accounts(iam, project_id)
    load_service_accounts(neo4j_session, accounts, project_id, gcp_update_tag)
    cleanup_iam(neo4j_session, common_job_parameters)

import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.keyvault import KeyVaultManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_key_vaults(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_key_vaults_tx, subscription_id, data_list, update_tag)


@timeit
def get_key_vaults_client(credentials: Credentials, subscription_id: str) -> KeyVaultManagementClient:
    client = KeyVaultManagementClient(credentials, subscription_id)
    return client


@timeit
def get_key_vaults_list(client: KeyVaultManagementClient, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        key_vaults_list = list(map(lambda x: x.as_dict(), client.vaults.list()))
        key_vaults_data = []
        for vault in key_vaults_list:
            x = vault['id'].split('/')
            vault['resource_group'] = x[x.index('resourceGroups') + 1]
            vault['consolelink'] = azure_console_link.get_console_link(
                id=vault['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
            if regions is None:
                key_vaults_data.append(vault)
            else:
                if vault.get('location') in regions or vault.get('location') == 'global':
                    key_vaults_data.append(vault)
        return key_vaults_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving key vaults - {e}")
        return []


def _load_key_vaults_tx(
    tx: neo4j.Transaction, subscription_id: str, key_vaults_list: List[Dict], update_tag: int,
) -> None:
    ingest_vault = """
    UNWIND {key_vaults_list} AS vault
    MERGE (k:AzureKeyVault{id: vault.id})
    ON CREATE SET k.firstseen = timestamp(),
    k.type = vault.type,
    k.location = vault.location,
    k.region = vault.location,
    k.consolelink = vault.consolelink,
    k.resourcegroup = vault.resource_group
    SET k.lastupdated = {update_tag},
    k.name = vault.name
    WITH k
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(k)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    tx.run(
        ingest_vault,
        key_vaults_list=key_vaults_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_key_vaults(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_key_vaults_cleanup.json', neo4j_session, common_job_parameters)


def sync_key_vaults(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list
) -> None:
    client = get_key_vaults_client(credentials, subscription_id)
    key_vaults_list = get_key_vaults_list(client, regions, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('key_vaults', None):
        pageNo = common_job_parameters.get("pagination", {}).get("key_vaults", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("key_vaults", None)["pageSize"]
        totalPages = len(key_vaults_list) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for key_vaults {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('key_vaults', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('key_vaults', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('key_vaults', {})['pageSize']
        if page_end > len(key_vaults_list) or page_end == len(key_vaults_list):
            key_vaults_list = key_vaults_list[page_start:]
        else:
            has_next_page = True
            key_vaults_list = key_vaults_list[page_start:page_end]
            common_job_parameters['pagination']['key_vaults']['hasNextPage'] = has_next_page

    load_key_vaults(neo4j_session, subscription_id, key_vaults_list, update_tag)
    cleanup_key_vaults(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, region: list
) -> None:
    logger.info("Syncing key vaults for subscription '%s'.", subscription_id)

    sync_key_vaults(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, region)

import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from cloudconsolelink.clouds.azure import AzureLinker
from  azure.mgmt.security import SecurityCenter

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()

def load_security_contacts(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_security_contacts_tx, subscription_id, data_list, update_tag)

def get_security_center_client(credentials: Credentials, subscription_id: str, region: str):
    client = client=SecurityCenter(credentials,subscription_id,region)
    return client

@timeit
def get_security_contacts_list(client: SecurityCenter) -> List[Dict]:
    try:
        security_contacts = list(map(lambda x:x.as_dict(), client.security_contacts.list()))
        return security_contacts

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving security contacts - {e}")
        return []

@timeit
def transform_security_contacts(security_contacts: List[Dict], subscription_id: str, common_job_parameters: str):

    security_contacts_data = []
    for contact in security_contacts:
        x = contact['id'].split('/')
        contact['resource_group'] = x[x.index('resourceGroups') + 1]
        contact['subscriptionid']=subscription_id
        contact['consolelink'] = azure_console_link.get_console_link(
            id=contact['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'])
        security_contacts_data.append(contact)
    return security_contacts_data

@timeit
def _load_security_contacts_tx(
    tx: neo4j.Transaction, subscription_id: str, security_contacts: List[Dict], update_tag: int,
) -> None:
    ingest_contacts = """
    UNWIND {CONTACTS} as cont
    MERGE (c:AzureSecurityContact{id: cont.id})
    ON CREATE SET c.firstseen = timestamp(),
    c.name = cont.name,
    c.consolelink = cont.consolelink,
    c.phone = cont.phone
    SET c.lastupdated = {update_tag}
    WITH c
    MATCH (owner:AzureSubscription{id: {SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(c)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """
    tx.run(
        ingest_contacts,
        CONTACTS = security_contacts,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )

def cleanup_security_contacts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_security_contacts_cleanup.json', neo4j_session, common_job_parameters)

def sync_security_contacts(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: List
) -> None:

    for region in regions:
        client = get_security_center_client(credentials, subscription_id, region)
        contacts = get_security_contacts_list(client)
        security_contacts_list = transform_security_contacts(contacts, subscription_id, common_job_parameters)

        if common_job_parameters.get('pagination', {}).get('security_contacts', None):
            pageNo = common_job_parameters.get("pagination", {}).get("security_contacts", None)["pageNo"]
            pageSize = common_job_parameters.get("pagination", {}).get("security_contacts", None)["pageSize"]
            totalPages = len(security_contacts_list) / pageSize
            if int(totalPages) != totalPages:
                totalPages = totalPages + 1
            totalPages = int(totalPages)
            if pageNo < totalPages or pageNo == totalPages:
                logger.info(f'pages process for security_contacts {pageNo}/{totalPages} pageSize is {pageSize}')
            page_start = (common_job_parameters.get('pagination', {}).get('security_contacts', {})[
                            'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('security_contacts', {})['pageSize']
            page_end = page_start + common_job_parameters.get('pagination', {}).get('security_contacts', {})['pageSize']
            if page_end > len(security_contacts_list) or page_end == len(security_contacts_list):
                security_contacts_list = security_contacts_list[page_start:]
            else:
                has_next_page = True
                security_contacts_list = security_contacts_list[page_start:page_end]
                common_job_parameters['pagination']['secuirty_contacts']['hasNextPage'] = has_next_page

        load_security_contacts(neo4j_session, subscription_id, security_contacts_list, update_tag)
        cleanup_security_contacts(neo4j_session, common_job_parameters)

@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: List
) -> None:
    logger.info("Syncing key Security Contacts for subscription '%s'.", subscription_id)

    sync_security_contacts(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)

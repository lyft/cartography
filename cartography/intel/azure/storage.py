import logging
from azure.mgmt.storage import StorageManagementClient
from cartography.util import get_optional_value
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(credentials, subscription_id):
    """
    Getting the Azure Storage client
    """
    client = StorageManagementClient(credentials, subscription_id)
    return client


@timeit
def get_storage_account_list(credentials, subscription_id):
    """
    Getting the list of storage accounts
    """
    try:
        client = get_client(credentials, subscription_id)
        storage_account_list = list(map(lambda x: x.as_dict(), client.storage_accounts.list()))

    except Exception as e:
        logger.warning("Error while retrieving storage accounts - {}".format(e))
        return []

    for storage_account in storage_account_list:
        x = storage_account['id'].split('/')
        storage_account['resourceGroup'] = x[x.index('resourceGroups')+1]

    return storage_account_list


@timeit
def load_storage_account_data(neo4j_session, subscription_id, storage_account_list, azure_update_tag):
    """
    Ingest Storage Account details into neo4j.
    """
    ingest_storage_account = """
    UNWIND {storage_accounts_list} as account
    MERGE (s:AzureStorageAccount{id: account.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.name = account.name, s.resourcegroup = account.resourceGroup,
    s.location = account.location
    SET s.lastupdated = {azure_update_tag},
    s.kind = account.kind,
    s.type = account.type,
    s.creationtime = account.creation_time,
    s.hnsenabled = account.is_hns_enabled,
    s.primarylocation = account.primary_location,
    s.secondarylocation = account.secondary_location,
    s.provisioningstate = account.provisioning_state,
    s.statusofprimary = account.status_of_primary,
    s.statusofsecondary = account.status_of_secondary,
    s.supportshttpstrafficonly = account.enable_https_traffic_only
    WITH s
    MATCH (owner:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_storage_account,
        storage_accounts_list=storage_account_list,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def sync_storage_account_details(neo4j_session, credentials, subscription_id, storage_account_list, sync_tag):
    details = get_storage_account_details(credentials, subscription_id, storage_account_list)
    load_storage_account_details(neo4j_session, credentials, subscription_id, details, sync_tag)


@timeit
def get_storage_account_details(credentials, subscription_id, storage_account_list):
    """
    Iterates over all Storage Accounts to get the different storage services.
    """
    for storage_account in storage_account_list:
        queue_services = get_queue_services(credentials, subscription_id, storage_account)
        table_services = get_table_services(credentials, subscription_id, storage_account)
        file_services = get_file_services(credentials, subscription_id, storage_account)
        blob_services = get_blob_services(credentials, subscription_id, storage_account)
        yield storage_account['id'], storage_account['name'], storage_account['resourceGroup'], queue_services, table_services, file_services, blob_services


@timeit
def get_queue_services(credentials, subscription_id, storage_account):
    """
    Gets the list of queue services.
    """
    try:
        client = get_client(credentials, subscription_id)
        queue_service_list = client.queue_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving queue services list - {}".format(e))
        return []

    return queue_service_list


@timeit
def get_table_services(credentials, subscription_id, storage_account):
    """
    Gets the list of table services.
    """
    try:
        client = get_client(credentials, subscription_id)
        table_service_list = client.table_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving table services list - {}".format(e))
        return []

    return table_service_list


@timeit
def get_file_services(credentials, subscription_id, storage_account):
    """
    Gets the list of file services.
    """
    try:
        client = get_client(credentials, subscription_id)
        file_service_list = client.file_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving file services list - {}".format(e))
        return []

    return file_service_list


@timeit
def get_blob_services(credentials, subscription_id, storage_account):
    """
    Gets the list of blob services.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_service_list = list(map(lambda x: x.as_dict(), client.blob_services.list(storage_account['resourceGroup'], storage_account['name'])))

    except Exception as e:
        logger.warning("Error while retrieving blob services list - {}".format(e))
        return []

    return blob_service_list


@timeit
def load_storage_account_details(neo4j_session, credentials, subscription_id, details, update_tag):
    """
    Create dictionaries for every Azure storage service so we can import them in a single query
    """
    queue_services = []
    table_services = []
    file_services = []
    blob_services = []

    for account_id, name, resourceGroup, queue_service, table_service, file_service, blob_service in details:
        if len(queue_service) > 0:
            for service in queue_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
            queue_services.extend(queue_service)

        if len(table_service) > 0:
            for service in table_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
            table_services.extend(table_service)

        if len(file_service) > 0:
            for service in file_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
            file_services.extend(file_service)

        if len(blob_service) > 0:
            for service in blob_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
            blob_services.extend(blob_service)

    _load_queue_services(neo4j_session, queue_services, update_tag)
    _load_table_services(neo4j_session, table_services, update_tag)
    _load_file_services(neo4j_session, file_services, update_tag)
    _load_blob_services(neo4j_session, blob_services, update_tag)

    sync_queue_services_details(neo4j_session, credentials, subscription_id, queue_services, update_tag)
    sync_table_services_details(neo4j_session, credentials, subscription_id, table_services, update_tag)
    sync_file_services_details(neo4j_session, credentials, subscription_id, file_services, update_tag)
    sync_blob_services_details(neo4j_session, credentials, subscription_id, blob_services, update_tag)


@timeit
def _load_queue_services(neo4j_session, queue_services, update_tag):
    """
    Ingest Queue Service details into neo4j.
    """
    ingest_queue_services = """
    UNWIND {queue_services_list} as qservice
    MERGE (qs:AzureStorageQueueService{id: qservice.id})
    ON CREATE SET qs.firstseen = timestamp(), qs.lastupdated = {azure_update_tag}
    SET qs.name = qservice.name,
    qs.type = qservice.type
    WITH qs, qservice
    MATCH (s:AzureStorageAccount{id: qservice.storage_account_id})
    MERGE (s)-[r:USES]->(qs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_queue_services,
        queue_services_list=queue_services,
        azure_update_tag=update_tag,
    )


@timeit
def _load_table_services(neo4j_session, table_services, update_tag):
    """
    Ingest Table Service details into neo4j.
    """
    ingest_table_services = """
    UNWIND {table_services_list} as tservice
    MERGE (ts:AzureStorageTableService{id: tservice.id})
    ON CREATE SET ts.firstseen = timestamp(), ts.lastupdated = {azure_update_tag}
    SET ts.name = tservice.name,
    ts.type = tservice.type
    WITH ts, tservice
    MATCH (s:AzureStorageAccount{id: tservice.storage_account_id})
    MERGE (s)-[r:USES]->(ts)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_table_services,
        table_services_list = table_services,
        azure_update_tag=update_tag,
    )


@timeit
def _load_file_services(neo4j_session, file_services, update_tag):
    """
    Ingest File Service details into neo4j.
    """
    ingest_file_services = """
    UNWIND {file_services_list} as fservice
    MERGE (fs:AzureStorageFileService{id: fservice.id})
    ON CREATE SET fs.firstseen = timestamp(), fs.lastupdated = {azure_update_tag}
    SET fs.name = fservice.name,
    fs.type = fservice.type
    WITH fs, fservice
    MATCH (s:AzureStorageAccount{id: fservice.storage_account_id})
    MERGE (s)-[r:USES]->(fs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_file_services,
        file_services_list=file_services,
        azure_update_tag=update_tag,
    )


@timeit
def _load_blob_services(neo4j_session, blob_services, update_tag):
    """
    Ingest Blob Service details into neo4j.
    """
    ingest_blob_services = """
    UNWIND {blob_services_list} as bservice
    MERGE (bs:AzureStorageBlobService{id: bservice.id})
    ON CREATE SET bs.firstseen = timestamp(), bs.lastupdated = {azure_update_tag}
    SET bs.name = bservice.name,
    bs.type = bservice.type
    WITH bs, bservice
    MATCH (s:AzureStorageAccount{id: bservice.storage_account_id})
    MERGE (s)-[r:USES]->(bs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_blob_services,
        blob_services_list=blob_services,
        azure_update_tag=update_tag,
    )


@timeit
def sync_queue_services_details(neo4j_session, credentials, subscription_id, queue_services, update_tag):
    queue_services_details = get_queue_services_details(credentials, subscription_id, queue_services)
    load_queue_services_details(neo4j_session, queue_services_details, update_tag)


@timeit
def get_queue_services_details(credentials, subscription_id, queue_services):
    """
    Returning the queues with their respective queue service id.
    """
    for queue_service in queue_services:
        queues = get_queues(credentials, subscription_id, queue_service)
        yield queue_service['id'], queues


@timeit
def get_queues(credentials, subscription_id, queue_service):
    """
    Getting the queues from the queue service.
    """
    try:
        client = get_client(credentials, subscription_id)
        queues = list(map(lambda x: x.as_dict(), client.queue.list(queue_service['resource_group_name'], queue_service['storage_account_name'])))

    except Exception as e:
        logger.warning("Error while retrieving queues - {}".format(e))
        return []

    return queues


@timeit
def load_queue_services_details(neo4j_session, details, update_tag):
    """
    Create dictionary for the queue so we can import them in a single query
    """
    queues = []

    for queue_service_id, queue in details:
        if len(queue) > 0:
            for q in queue:
                q['service_id'] = queue_service_id
            queues.extend(queue)

    _load_queues(neo4j_session, queues, update_tag)


@timeit
def _load_queues(neo4j_session, queues, update_tag):
    """
    Ingest Queue details into neo4j.
    """
    ingest_queues = """
    UNWIND {queues_list} as queue
    MERGE (q:AzureStorageQueue{id: queue.id})
    ON CREATE SET q.firstseen = timestamp(), q.lastupdated = {azure_update_tag}
    SET q.name = queue.name,
    q.type = queue.type
    WITH q, queue
    MATCH (qs:AzureStorageQueueService{id: queue.service_id})
    MERGE (qs)-[r:CONTAINS]->(q)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_queues,
        queues_list=queues,
        azure_update_tag=update_tag,
    )


@timeit
def sync_table_services_details(neo4j_session, credentials, subscription_id, table_services, update_tag):
    table_services_details = get_table_services_details(credentials, subscription_id, table_services)
    load_table_services_details(neo4j_session, table_services_details, update_tag)


@timeit
def get_table_services_details(credentials, subscription_id, table_services):
    """
    Returning the tables with their respective table service id.
    """
    for table_service in table_services:
        tables = get_tables(credentials, subscription_id, table_service)
        yield table_service['id'], tables


@timeit
def get_tables(credentials, subscription_id, table_service):
    """
    Getting the tables from the table service.
    """
    try:
        client = get_client(credentials, subscription_id)
        tables = list(map(lambda x: x.as_dict(), client.table.list(table_service['resource_group_name'], table_service['storage_account_name'])))

    except Exception as e:
        logger.warning("Error while retrieving tables - {}".format(e))
        return []

    return tables


@timeit
def load_table_services_details(neo4j_session, details, update_tag):
    """
    Create dictionary for the table so we can import them in a single query
    """
    tables = []

    for table_service_id, table in details:
        if len(table) > 0:
            for t in table:
                t['service_id'] = table_service_id
            tables.extend(table)

    _load_tables(neo4j_session, tables, update_tag)


@timeit
def _load_tables(neo4j_session, tables, update_tag):
    """
    Ingest Table details into neo4j.
    """
    ingest_tables = """
    UNWIND {tables_list} as table
    MERGE (t:AzureStorageTable{id: table.id})
    ON CREATE SET t.firstseen = timestamp(), t.lastupdated = {azure_update_tag}
    SET t.name = table.name,
    t.type = table.type
    WITH t, table
    MATCH (ts:AzureStorageTableService{id: table.service_id})
    MERGE (ts)-[r:CONTAINS]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_tables,
        tables_list=tables,
        azure_update_tag=update_tag,
    )


@timeit
def sync_file_services_details(neo4j_session, credentials, subscription_id, file_services, update_tag):
    file_services_details = get_file_services_details(credentials, subscription_id, file_services)
    load_file_services_details(neo4j_session, file_services_details, update_tag)


@timeit
def get_file_services_details(credentials, subscription_id, file_services):
    """
    Returning the shares with their respective file service id.
    """
    for file_service in file_services:
        shares = get_shares(credentials, subscription_id, file_service)
        yield file_service['id'], shares


@timeit
def get_shares(credentials, subscription_id, file_service):
    """
    Getting the shares from the file service.
    """
    try:
        client = get_client(credentials, subscription_id)
        shares = list(map(lambda x: x.as_dict(), client.file_shares.list(file_service['resource_group_name'], file_service['storage_account_name'])))

    except Exception as e:
        logger.warning("Error while retrieving file shares - {}".format(e))
        return []

    return shares


@timeit
def load_file_services_details(neo4j_session, details, update_tag):
    """
    Create dictionary for the shares so we can import them in a single query
    """
    shares = []

    for file_service_id, share in details:
        if len(share) > 0:
            for s in share:
                s['service_id'] = file_service_id
            shares.extend(share)

    _load_shares(neo4j_session, shares, update_tag)


@timeit
def _load_shares(neo4j_session, shares, update_tag):
    """
    Ingest Share details into neo4j.
    """
    ingest_shares = """
    UNWIND {shares_list} as s
    MERGE (share:AzureStorageFileShare{id: s.id})
    ON CREATE SET share.firstseen = timestamp(), share.lastupdated = {azure_update_tag}
    SET share.name = s.name,
    share.type = s.type,
    share.lastmodifiedtime = s.last_modified_time,
    share.sharequota = s.share_quota,
    share.accesstier = s.access_tier,
    share.deleted = s.deleted,
    share.accesstierchangetime = s.access_tier_change_time,
    share.accesstierstatus = s.access_tier_status,
    share.deletedtime = s.deleted_time,
    share.enabledProtocols = s.enabled_protocols,
    share.remainingretentiondays = s.remaining_retention_days,
    share.shareusagebytes = s.share_usage_bytes,
    share.version = s.version
    WITH share, s
    MATCH (fs:AzureStorageFileService{id: s.service_id})
    MERGE (fs)-[r:CONTAINS]->(share)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_shares,
        shares_list=shares,
        azure_update_tag=update_tag,
    )


@timeit
def sync_blob_services_details(neo4j_session, credentials, subscription_id, blob_services, update_tag):
    blob_services_details = get_blob_services_details(credentials, subscription_id, blob_services)
    load_blob_services_details(neo4j_session, blob_services_details, update_tag)


@timeit
def get_blob_services_details(credentials, subscription_id, blob_services):
    """
    Returning the blob containers with their respective blob service id.
    """
    for blob_service in blob_services:
        blob_containers = get_blob_containers(credentials, subscription_id, blob_service)
        yield blob_service['id'], blob_containers


@timeit
def get_blob_containers(credentials, subscription_id, blob_service):
    """
    Getting the blob containers from the blob service.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_containers = list(map(lambda x: x.as_dict(), client.blob_containers.list(blob_service['resource_group_name'], blob_service['storage_account_name'])))

    except Exception as e:
        logger.warning("Error while retrieving blob_containers - {}".format(e))
        return []

    return blob_containers


@timeit
def load_blob_services_details(neo4j_session, details, update_tag):
    """
    Create dictionary for the blob containers so we can import them in a single query
    """
    blob_containers = []

    for blob_service_id, container in details:
        if len(container) > 0:
            for c in container:
                c['service_id'] = blob_service_id
            blob_containers.extend(container)

    _load_blob_containers(neo4j_session, blob_containers, update_tag)


@timeit
def _load_blob_containers(neo4j_session, blob_containers, update_tag):
    """
    Ingest Blob Container details into neo4j.
    """
    ingest_blob_containers = """
    UNWIND {blob_containers_list} as blob
    MERGE (bc:AzureStorageBlobContainer{id: blob.id})
    ON CREATE SET bc.firstseen = timestamp(), bc.lastupdated = {azure_update_tag}
    SET bc.name = blob.name,
    bc.type = blob.type,
    bc.deleted = blob.deleted,
    bc.deletedtime = blob.deleted_time,
    bc.defaultencryptionscope = blob.default_encryption_scope,
    bc.publicaccess = blob.public_access,
    bc.leasestatus = blob.lease_status,
    bc.leasestate = blob.lease_state,
    bc.lastmodifiedtime = blob.last_modified_time,
    bc.remainingretentiondays = blob.remaining_retention_days,
    bc.version = blob.version,
    bc.immutabilitypolicy = blob.has_immutability_policy,
    bc.haslegalhold = blob.has_legal_hold,
    bc.leaseduration = blob.leaseDuration
    WITH bc, blob
    MATCH (bs:AzureStorageBlobService{id: blob.service_id})
    MERGE (bs)-[r:CONTAINS]->(bc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_blob_containers,
        blob_containers_list=blob_containers,
        azure_update_tag=update_tag,
    )


@timeit
def cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_storage_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure Storage for subscription '%s'.", subscription_id)
    storage_account_list = get_storage_account_list(credentials, subscription_id)
    load_storage_account_data(neo4j_session, subscription_id, storage_account_list, sync_tag)
    sync_storage_account_details(neo4j_session, credentials, subscription_id, storage_account_list, sync_tag)
    cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters)

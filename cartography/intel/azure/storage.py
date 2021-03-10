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
    MERGE (s:AzureStorageAccount{id: {AccountId}})
    ON CREATE SET s.firstseen = timestamp(),
    s.id = {AccountId}, s.name = {Name},
    s.resourcegroup = {ResourceGroup}, s.location = {Location}
    SET s.lastupdated = {azure_update_tag},
    s.kind = {Kind},
    s.type = {Type},
    s.creationtime = {CreationTime},
    s.hnsenabled = {HnsEnabled},
    s.primarylocation = {PrimaryLocation},
    s.secondarylocation = {SecondaryLocation},
    s.provisioningstate = {ProvisioningState},
    s.statusofprimary = {StatusOfPrimary},
    s.statusofsecondary = {StatusOfSecondary},
    s.supportshttpstrafficonly = {SupportsHttpsTrafficOnly}
    WITH s
    MATCH (owner:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for storage_account in storage_account_list:
        neo4j_session.run(
            ingest_storage_account,
            AccountId=storage_account['id'],
            Name=storage_account['name'],
            ResourceGroup=storage_account['resourceGroup'],
            Location=storage_account['location'],
            Kind=storage_account['kind'],
            Type=storage_account['type'],
            CreationTime=storage_account['creation_time'],
            HnsEnabled=get_optional_value(storage_account, ["is_hns_enabled"]),
            PrimaryLocation=storage_account['primary_location'],
            SecondaryLocation=get_optional_value(storage_account, ["secondary_location"]),
            ProvisioningState=storage_account['provisioning_state'],
            StatusOfPrimary=storage_account['status_of_primary'],
            StatusOfSecondary=get_optional_value(storage_account, ["status_of_secondary"]),
            SupportsHttpsTrafficOnly=storage_account['enable_https_traffic_only'],
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
    MERGE (qs:AzureStorageQueueService{id: {QueueServiceId}})
    ON CREATE SET qs.firstseen = timestamp(), qs.lastupdated = {azure_update_tag}
    SET qs.name = {Name},
    qs.type = {Type}
    WITH qs
    MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
    MERGE (s)-[r:USES]->(qs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for service in queue_services:
        neo4j_session.run(
            ingest_queue_services,
            QueueServiceId=service['id'],
            Name=service['name'],
            Type=service['type'],
            StorageAccountId=service['storage_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_table_services(neo4j_session, table_services, update_tag):
    """
    Ingest Table Service details into neo4j.
    """
    ingest_table_services = """
    MERGE (ts:AzureStorageTableService{id: {TableServiceId}})
    ON CREATE SET ts.firstseen = timestamp(), ts.lastupdated = {azure_update_tag}
    SET ts.name = {Name},
    ts.type = {Type}
    WITH ts
    MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
    MERGE (s)-[r:USES]->(ts)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for service in table_services:
        neo4j_session.run(
            ingest_table_services,
            TableServiceId=service['id'],
            Name=service['name'],
            Type=service['type'],
            StorageAccountId=service['storage_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_file_services(neo4j_session, file_services, update_tag):
    """
    Ingest File Service details into neo4j.
    """
    ingest_file_services = """
    MERGE (fs:AzureStorageFileService{id: {FileServiceId}})
    ON CREATE SET fs.firstseen = timestamp(), fs.lastupdated = {azure_update_tag}
    SET fs.name = {Name},
    fs.type = {Type}
    WITH fs
    MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
    MERGE (s)-[r:USES]->(fs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for service in file_services:
        neo4j_session.run(
            ingest_file_services,
            FileServiceId=service['id'],
            Name=service['name'],
            Type=service['type'],
            StorageAccountId=service['storage_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_blob_services(neo4j_session, blob_services, update_tag):
    """
    Ingest Blob Service details into neo4j.
    """
    ingest_blob_services = """
    MERGE (bs:AzureStorageBlobService{id: {BlobServiceId}})
    ON CREATE SET bs.firstseen = timestamp(), bs.lastupdated = {azure_update_tag}
    SET bs.name = {Name},
    bs.type = {Type}
    WITH bs
    MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
    MERGE (s)-[r:USES]->(bs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for service in blob_services:
        neo4j_session.run(
            ingest_blob_services,
            BlobServiceId=service['id'],
            Name=service['name'],
            Type=service['type'],
            StorageAccountId=service['storage_account_id'],
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
    MERGE (q:AzureStorageQueue{id: {QueueId}})
    ON CREATE SET q.firstseen = timestamp(), q.lastupdated = {azure_update_tag}
    SET q.name = {Name},
    q.type = {Type}
    WITH q
    MATCH (qs:AzureStorageQueueService{id: {ServiceId}})
    MERGE (qs)-[r:CONTAINS]->(q)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for queue in queues:
        neo4j_session.run(
            ingest_queues,
            QueueId=queue['id'],
            Name=queue['name'],
            Type=queue['type'],
            ServiceId=queue['service_id'],
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
    MERGE (t:AzureStorageTable{id: {TableId}})
    ON CREATE SET t.firstseen = timestamp(), t.lastupdated = {azure_update_tag}
    SET t.name = {Name},
    t.type = {Type}
    WITH t
    MATCH (ts:AzureStorageTableService{id: {ServiceId}})
    MERGE (ts)-[r:CONTAINS]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for table in tables:
        neo4j_session.run(
            ingest_tables,
            TableId=table['id'],
            Name=table['name'],
            Type=table['type'],
            ServiceId=table['service_id'],
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
    MERGE (share:AzureStorageFileShare{id: {ShareId}})
    ON CREATE SET share.firstseen = timestamp(), share.lastupdated = {azure_update_tag}
    SET share.name = {Name},
    share.type = {Type},
    share.lastmodifiedtime = {LastModifiedTime},
    share.sharequota = {ShareQuota},
    share.accesstier = {AccessTier},
    share.deleted = {Deleted},
    share.accesstierchangetime = {AccessTierChangeTime},
    share.accesstierstatus = {AccessTierStatus},
    share.deletedtime = {DeletedTime},
    share.enabledProtocols = {EnabledProtocols},
    share.remainingretentiondays = {RemainingRetentionDays},
    share.shareusagebytes = {ShareUsageBytes},
    share.version = {Version}
    WITH share
    MATCH (fs:AzureStorageFileService{id: {ServiceId}})
    MERGE (fs)-[r:CONTAINS]->(share)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for share in shares:
        neo4j_session.run(
            ingest_shares,
            ShareId=share['id'],
            Name=share['name'],
            Type=share['type'],
            LastModifiedTime=share['last_modified_time'],
            ShareQuota=share['share_quota'],
            AccessTier=share['access_tier'],
            Deleted=get_optional_value(share, ['deleted']),
            AccessTierChangeTime=get_optional_value(share, ['access_tier_change_time']),
            AccessTierStatus=get_optional_value(share, ['access_tier_status']),
            DeletedTime=get_optional_value(share, ['deleted_time']),
            EnabledProtocols=get_optional_value(share, ['enabled_protocols']),
            RemainingRetentionDays=get_optional_value(share, ['remaining_retention_days']),
            ShareUsageBytes=get_optional_value(share, ['share_usage_bytes']),
            Version=get_optional_value(share, ['version']),
            ServiceId=get_optional_value(share, ['service_id']),
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
    MERGE (bc:AzureStorageBlobContainer{id: {ContainerId}})
    ON CREATE SET bc.firstseen = timestamp(), bc.lastupdated = {azure_update_tag}
    SET bc.name = {Name},
    bc.type = {Type},
    bc.deleted = {Deleted},
    bc.deletedtime = {DeletedTime},
    bc.defaultencryptionscope = {DefaultEncryptionScope},
    bc.publicaccess = {PublicAccess},
    bc.leasestatus = {LeaseStatus},
    bc.leasestate = {LeaseState},
    bc.lastmodifiedtime = {LastModifiedTime},
    bc.remainingretentiondays = {RemainingRetentionDays},
    bc.version = {Version},
    bc.immutabilitypolicy = {HasImmutatbilityPolicy},
    bc.haslegalhold = {HasLegalHold},
    bc.leaseduration = {LeaseDuration}
    WITH bc
    MATCH (bs:AzureStorageBlobService{id: {ServiceId}})
    MERGE (bs)-[r:CONTAINS]->(bc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for container in blob_containers:
        neo4j_session.run(
            ingest_blob_containers,
            ContainerId=container['id'],
            Name=container['name'],
            Type=container['type'],
            Deleted=container['deleted'],
            DeletedTime=get_optional_value(container, ['deleted_time']),
            DefaultEncryptionScope=container['default_encryption_scope'],
            PublicAccess=container['public_access'],
            LeaseStatus=container['lease_status'],
            LeaseState=container['lease_state'],
            LastModifiedTime=container['last_modified_time'],
            RemainingRetentionDays=container['remaining_retention_days'],
            Version=get_optional_value(container, ['version']),
            HasImmutatbilityPolicy=container['has_immutability_policy'],
            HasLegalHold=container['has_legal_hold'],
            LeaseDuration=get_optional_value(container, ['leaseDuration']),
            ServiceId=container['service_id'],
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

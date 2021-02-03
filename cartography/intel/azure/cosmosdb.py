import logging
import uuid
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(credentials, subscription_id):
    """
    Getting the CosmosDB client
    """
    client = CosmosDBManagementClient(credentials, subscription_id)
    return client


@timeit
def get_database_account_list(credentials, subscription_id):
    """
    Get a list of all database accounts.
    """
    try:
        client = get_client(credentials, subscription_id)
        database_account_list = list(map(lambda x: x.as_dict(), client.database_accounts.list()))

    except Exception as e:
        logger.warning("Error while retrieving database accounts - {}".format(e))
        return []

    for database_account in database_account_list:
        x = database_account['id'].split('/')
        database_account['resourceGroup'] = x[x.index('resourceGroups')+1]

    return database_account_list


@timeit
def load_database_account_data(neo4j_session, subscription_id, database_account_list, azure_update_tag):
    """
    Ingest data of all database accounts into neo4j.
    """
    ingest_database_account = """
    MERGE (d:AzureDatabaseAccount{id: {AccountId}})
    ON CREATE SET d.firstseen = timestamp(),
    d.id = {AccountId}, d.name = {Name},
    d.resourcegroup = {ResourceGroup}, d.location = {Location}
    SET d.lastupdated = {azure_update_tag},
    d.kind = {Kind},
    d.type = {Type},
    d.ipranges = coalesce(d.ipranges, []) + {IpRanges},
    d.capabilities = {Capabilities},
    d.documentendpoint = {DocumentEndpoint},
    d.virtualnetworkfilterenabled = {VirtualNetworkFilterEnabled},
    d.enableautomaticfailover = {EnableAutomaticFailover},
    d.provisioningstate = {ProvisioningState},
    d.multiplewritelocations = {MultipleWriteLocations},
    d.accountoffertype = {AccountOfferType},
    d.publicnetworkaccess = {PublicNetworkAccess},
    d.enablecassandraconnector = {EnableCassandraConnector},
    d.connectoroffer = {ConnectorOffer},
    d.disablekeybasedmetadatawriteaccess = {DisableKeyBasedMetadataWriteAccess},
    d.keyvaulturi = {KeyVaultUri},
    d.enablefreetier = {EnableFreeTier},
    d.enableanalyticalstorage = {EnableAnalyticalStorage},
    d.defaultconsistencylevel = {DefaultConsistencyLevel},
    d.maxstalenessprefix = {MaxStalenessPrefix},
    d.maxintervalinseconds = {MaxIntervalInSeconds}
    WITH d
    MATCH (owner:AzureAccount{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for database_account in database_account_list:
        capabilities = []
        if 'capabilities' in database_account and len(database_account['capabilities']) > 0:
            capabilities = database_account['capabilities'].values()
        neo4j_session.run(
            ingest_database_account,
            AccountId=database_account['id'],
            Name=database_account['name'],
            ResourceGroup=database_account['resourceGroup'],
            Location=database_account['location'],
            Kind=database_account['kind'],
            Type=database_account['type'],
            IpRanges=database_account.get('ip_rules'),
            Capabilities=capabilities,
            DocumentEndpoint=database_account['document_endpoint'],
            VirtualNetworkFilterEnabled=database_account['is_virtual_network_filter_enabled'],
            EnableAutomaticFailover=database_account['enable_automatic_failover'],
            ProvisioningState=database_account['provisioning_state'],
            MultipleWriteLocations=database_account['enable_multiple_write_locations'],
            AccountOfferType=database_account['database_account_offer_type'],
            PublicNetworkAccess=database_account['public_network_access'],
            EnableCassandraConnector=database_account['enable_cassandra_connector'],
            ConnectorOffer=database_account['connector_offer'],
            DisableKeyBasedMetadataWriteAccess=database_account['disable_key_based_metadata_write_access'],
            KeyVaultUri=database_account['key_vault_key_uri'],
            EnableFreeTier=database_account['enable_free_tier'],
            EnableAnalyticalStorage=database_account['enable_analytical_storage'],
            ServerVersion=database_account['api_properties']['server_version'],
            DefaultConsistencyLevel=database_account.get('consistency_policy').get('default_consistency_level'),
            MaxStalenessPrefix=database_account.get('consistency_policy').get('max_staleness_prefix'),
            MaxIntervalInSeconds=database_account.get('consistency_policy').get('max_interval_in_seconds'),
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag,
        )

        # cleanup existing cors policy properties
        # TODO: Take a look at the JSON code
        run_cleanup_job(
            'azure_cosmosdb_cors_details.json',
            neo4j_session,
            {'UPDATE_TAG': azure_update_tag, 'AZURE_SUBSCRIPTION_ID': subscription_id, 'DATABASE_ACCOUNT_ID': database_account['id']},
        )

        if 'cors' in database_account and len(database_account['cors']) > 0:
            _load_cosmosdb_cors_policy(neo4j_session, database_account, azure_update_tag)
        if 'failover_policies' in database_account and len(database_account['failover_policies']) > 0:
            _load_cosmosdb_failover_policies(neo4j_session, database_account, azure_update_tag)
        if 'private_endpoint_connections' in database_account and len(database_account['private_endpoint_connections']) > 0:
            _load_cosmosdb_private_endpoint_connections(neo4j_session, database_account, azure_update_tag)
        if 'virtual_network_rules' in database_account and len(database_account['virtual_network_rules']) > 0:
            _load_cosmosdb_virtual_network_rules(neo4j_session, database_account, azure_update_tag)

        locations = []
        # Extracting every location
        if 'write_locations' in database_account and len(database_account['write_locations']) > 0:
            for loc in database_account['write_locations']:
                locations.append(loc)
        if 'read_locations' in database_account and len(database_account['read_locations']) > 0:
            for loc in database_account['read_locations']:
                locations.append(loc)
        if 'locations' in database_account and len(database_account['locations']) > 0:
            for loc in database_account['locations']:
                locations.append(loc)
        loc = [i for n, i in enumerate(locations) if i not in locations[n + 1:]]  # Selecting only the unique location entries
        if len(loc) > 0:
            _load_database_account_locations(neo4j_session, database_account, loc, azure_update_tag)


@timeit
def _load_database_account_locations(neo4j_session, database_account, locations, azure_update_tag):
    """
    Getting locations enabled with read/write permissions for the database account.
    """
    database_account_id = database_account['id']
    for loc in locations:
        if 'write_locations' in database_account and loc in database_account['write_locations']:
            _load_database_account_write_locations(neo4j_session, database_account_id, loc, azure_update_tag)
        if 'read_locations' in database_account and loc in database_account['read_locations']:
            _load_database_account_read_locations(neo4j_session, database_account_id, loc, azure_update_tag)
        if 'locations' in database_account and loc in database_account['locations']:
            _load_database_account_associated_locations(neo4j_session, database_account_id, loc, azure_update_tag)


@timeit
def _load_database_account_write_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of location with write permission enabled.
    """
    ingest_write_location = """
    MERGE (loc:AzureCosmosDBEnabledLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:WRITE_PERMISSIONS_FROM]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_write_location,
        LocationId=loc['id'],
        Name=loc.get('location_name'),
        DocumentEndpoint=loc.get('document_endpoint'),
        ProvisioningState=loc.get('provisioning_state'),
        FailoverPriority=loc.get('failover_priority'),
        IsZoneRedundant=loc.get('is_zone_redundant'),
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_database_account_read_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of location with read permission enabled.
    """
    ingest_read_location = """
    MERGE (loc:AzureCosmosDBEnabledLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:READ_PERMISSIONS_FROM]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_read_location,
        LocationId=loc['id'],
        Name=loc['location_name'],
        DocumentEndpoint=loc.get('document_endpoint'),
        ProvisioningState=loc.get('provisioning_state'),
        FailoverPriority=loc.get('failover_priority'),
        IsZoneRedundant=loc.get('is_zone_redundant'),
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_database_account_associated_locations(neo4j_session, database_account_id, loc, azure_update_tag):
    """
    Ingest the details of enabled location for the database account.
    """
    ingest_associated_location = """
    MERGE (loc:AzureCosmosDBEnabledLocation{id: {LocationId}})
    ON CREATE SET loc.firstseen = timestamp(), loc.locationname = {Name}
    SET loc.lastupdated = {azure_update_tag},
    loc.documentendpoint = {DocumentEndpoint},
    loc.provisioningstate = {ProvisioningState},
    loc.failoverpriority = {FailoverPriority},
    loc.iszoneredundant = {IsZoneRedundant}
    WITH loc
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:ASSOCIATED_WITH]->(loc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_associated_location,
        LocationId=loc['id'],
        Name=loc['location_name'],
        DocumentEndpoint=loc.get('document_endpoint'),
        ProvisioningState=loc.get('provisioning_state'),
        FailoverPriority=loc.get('failover_priority'),
        IsZoneRedundant=loc.get('is_zone_redundant'),
        DatabaseAccountId=database_account_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def _load_cosmosdb_cors_policy(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Cors Policy of the database account.
    """
    database_account_id = database_account['id']
    cors_policy_unique_id = uuid.uuid4()

    ingest_cors_policy = """
    MERGE (corspolicy:AzureCosmosDBCorsPolicy{id: {PolicyUniqueId}})
    ON CREATE SET corspolicy.firstseen = timestamp(), corspolicy.allowedorigins = {AllowedOrigins}
    SET corspolicy.lastupdated = {azure_update_tag},
    corspolicy.allowedmethods = {AllowedMethods},
    corspolicy.allowedheaders = {AllowedHeaders},
    corspolicy.exposedheaders = {ExposedHeaders},
    corspolicy.maxageinseconds = {MaxAgeInSeconds}
    WITH corspolicy
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(corspolicy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for policy in database_account['cors']:
        neo4j_session.run(
            ingest_cors_policy,
            PolicyUniqueId=cors_policy_unique_id,
            AllowedOrigins=policy['allowed_origins'],
            AllowedMethods=policy.get('allowed_methods'),
            AllowedHeaders=policy.get('allowed_headers'),
            ExposedHeaders=policy.get('exposed_headers'),
            MaxAgeInSeconds=policy.get('max_age_in_seconds'),
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )


@timeit
def _load_cosmosdb_failover_policies(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Failover Policies of the database account.
    """
    database_account_id = database_account['id']
    ingest_failover_policies = """
    MERGE (fpolicy:AzureDatabaseAccountFailoverPolicy{id: {FailoverPolicyId}})
    ON CREATE SET fpolicy.firstseen = timestamp()
    SET fpolicy.lastupdated = {azure_update_tag},
    fpolicy.locationname = {LocationName},
    fpolicy.failoverpriority = {FailoverPriority}
    WITH fpolicy
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(fpolicy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for policy in database_account['failover_policies']:
        neo4j_session.run(
            ingest_failover_policies,
            FailoverPolicyId=policy['id'],
            LocationName=policy.get('location_name'),
            FailoverPriority=policy.get('failover_priority'),
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )


@timeit
def _load_cosmosdb_private_endpoint_connections(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Private Endpoint Connections of the database account.
    """
    database_account_id = database_account['id']
    ingest_private_endpoint_connections = """
    MERGE (pec:AzureCosmosDBPrivateEndpointConnection{id: {PrivateEndpointConnectionId}})
    ON CREATE SET pec.firstseen = timestamp()
    SET pec.lastupdated = {azure_update_tag},
    pec.name = {Name},
    pec.privateendpointid = {PrivateEndpointId},
    pec.status = {Status},
    pec.actionrequired = {ActionRequired}
    WITH pec
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONFIGURED_WITH]->(pec)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for endpoint in database_account['private_endpoint_connections']:
        neo4j_session.run(
            ingest_private_endpoint_connections,
            PrivateEndpointConnectionId=endpoint['id'],
            Name=endpoint.get('name'),
            Status=endpoint.get('private_link_service_connection_state').get('status'),
            ActionRequired=endpoint.get('private_link_service_connection_state').get('actions_required'),
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )


@timeit
def _load_cosmosdb_virtual_network_rules(neo4j_session, database_account, azure_update_tag):
    """
    Ingest the details of the Virtual Network Rules of the database account.
    """
    database_account_id = database_account['id']
    ingest_virtual_network_rules = """
    MERGE (rules:AzureCosmosDBVirtualNetworkRule{id: {VirtualNetworkRuleId}})
    ON CREATE SET rules.firstseen = timestamp()
    SET rules.lastupdated = {azure_update_tag},
    rules.ignoremissingvnetserviceendpoint = {IgnoreMissingVNetServiceEndpoint}
    WITH rules
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONFIGURED_WITH]->(rules)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for rule in database_account['virtual_network_rules']:
        neo4j_session.run(
            ingest_virtual_network_rules,
            VirtualNetworkRuleId=rule['id'],
            IgnoreMissingVNetServiceEndpoint=rule.get('ignore_missing_v_net_service_endpoint'),
            DatabaseAccountId=database_account_id,
            azure_update_tag=azure_update_tag,
        )


# @timeit
# def sync_storage_account_details(neo4j_session, credentials, subscription_id, storage_account_list, sync_tag):
#     details = get_storage_account_details(credentials, subscription_id, storage_account_list)
#     load_storage_account_details(neo4j_session, credentials, subscription_id, details, sync_tag)
#
#
# @timeit
# def get_storage_account_details(credentials, subscription_id, storage_account_list):
#     for storage_account in storage_account_list:
#         queue_services = get_queue_services(credentials, subscription_id, storage_account)
#         table_services = get_table_services(credentials, subscription_id, storage_account)
#         file_services = get_file_services(credentials, subscription_id, storage_account)
#         blob_services = get_blob_services(credentials, subscription_id, storage_account)
#         yield storage_account['id'], storage_account['name'], storage_account['resourceGroup'], queue_services, table_services, file_services, blob_services
#
#
# @timeit
# def get_queue_services(credentials, subscription_id, storage_account):
#     try:
#         client = get_client(credentials, subscription_id)
#         queue_service_list = client.queue_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']
#
#     except Exception as e:
#         logger.warning("Error while retrieving queue services list - {}".format(e))
#         return []
#
#     return queue_service_list
#
#
# @timeit
# def get_table_services(credentials, subscription_id, storage_account):
#     try:
#         client = get_client(credentials, subscription_id)
#         table_service_list = client.table_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']
#
#     except Exception as e:
#         logger.warning("Error while retrieving table services list - {}".format(e))
#         return []
#
#     return table_service_list
#
#
# @timeit
# def get_file_services(credentials, subscription_id, storage_account):
#     try:
#         client = get_client(credentials, subscription_id)
#         file_service_list = client.file_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']
#
#     except Exception as e:
#         logger.warning("Error while retrieving file services list - {}".format(e))
#         return []
#
#     return file_service_list
#
#
# @timeit
# def get_blob_services(credentials, subscription_id, storage_account):
#     try:
#         client = get_client(credentials, subscription_id)
#         blob_service_list = list(map(lambda x: x.as_dict(), client.blob_services.list(storage_account['resourceGroup'], storage_account['name'])))
#
#         # blob_service_list = client.blob_services.list(storage_account['resourceGroup'], storage_account['name']).as_dict()['value']
#
#     except Exception as e:
#         logger.warning("Error while retrieving blob services list - {}".format(e))
#         return []
#
#     return blob_service_list
#
#
# @timeit
# def load_storage_account_details(neo4j_session, credentials, subscription_id, details, update_tag):
#     queue_services = []
#     table_services = []
#     file_services = []
#     blob_services = []
#
#     for account_id, name, resourceGroup, queue_service, table_service, file_service, blob_service in details:
#         if len(queue_service) > 0:
#             for service in queue_service:
#                 service['storage_account_name'] = name
#                 service['storage_account_id'] = account_id
#                 service['resource_group_name'] = resourceGroup
#             queue_services.extend(queue_service)
#
#         if len(table_service) > 0:
#             for service in table_service:
#                 service['storage_account_name'] = name
#                 service['storage_account_id'] = account_id
#                 service['resource_group_name'] = resourceGroup
#             table_services.extend(table_service)
#
#         if len(file_service) > 0:
#             for service in file_service:
#                 service['storage_account_name'] = name
#                 service['storage_account_id'] = account_id
#                 service['resource_group_name'] = resourceGroup
#             file_services.extend(file_service)
#
#         if len(blob_service) > 0:
#             for service in blob_service:
#                 service['storage_account_name'] = name
#                 service['storage_account_id'] = account_id
#                 service['resource_group_name'] = resourceGroup
#             blob_services.extend(blob_service)
#
#     _load_queue_services(neo4j_session, queue_services, update_tag)
#     _load_table_services(neo4j_session, table_services, update_tag)
#     _load_file_services(neo4j_session, file_services, update_tag)
#     _load_blob_services(neo4j_session, blob_services, update_tag)
#
#     sync_queue_services_details(neo4j_session, credentials, subscription_id, queue_services, update_tag)
#     sync_table_services_details(neo4j_session, credentials, subscription_id, table_services, update_tag)
#     sync_file_services_details(neo4j_session, credentials, subscription_id, file_services, update_tag)
#     sync_blob_services_details(neo4j_session, credentials, subscription_id, blob_services, update_tag)
#
#
# @timeit
# def _load_queue_services(neo4j_session, queue_services, update_tag):
#     ingest_queue_services = """
#     MERGE (qs:AzureStorageQueueService{id: {QueueServiceId}})
#     ON CREATE SET qs.firstseen = timestamp(), qs.lastupdated = {azure_update_tag}
#     SET qs.name = {Name},
#     qs.type = {Type}
#     WITH qs
#     MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
#     MERGE (s)-[r:USES]->(qs)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for service in queue_services:
#         neo4j_session.run(
#             ingest_queue_services,
#             QueueServiceId=service['id'],
#             Name=service['name'],
#             Type=service['type'],
#             StorageAccountId=service['storage_account_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def _load_table_services(neo4j_session, table_services, update_tag):
#     ingest_table_services = """
#     MERGE (ts:AzureStorageTableService{id: {TableServiceId}})
#     ON CREATE SET ts.firstseen = timestamp(), ts.lastupdated = {azure_update_tag}
#     SET ts.name = {Name},
#     ts.type = {Type}
#     WITH ts
#     MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
#     MERGE (s)-[r:USES]->(ts)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for service in table_services:
#         neo4j_session.run(
#             ingest_table_services,
#             TableServiceId=service['id'],
#             Name=service['name'],
#             Type=service['type'],
#             StorageAccountId=service['storage_account_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def _load_file_services(neo4j_session, file_services, update_tag):
#     ingest_file_services = """
#     MERGE (fs:AzureStorageFileService{id: {FileServiceId}})
#     ON CREATE SET fs.firstseen = timestamp(), fs.lastupdated = {azure_update_tag}
#     SET fs.name = {Name},
#     fs.type = {Type}
#     WITH fs
#     MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
#     MERGE (s)-[r:USES]->(fs)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for service in file_services:
#         neo4j_session.run(
#             ingest_file_services,
#             FileServiceId=service['id'],
#             Name=service['name'],
#             Type=service['type'],
#             StorageAccountId=service['storage_account_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def _load_blob_services(neo4j_session, blob_services, update_tag):
#     ingest_blob_services = """
#     MERGE (bs:AzureStorageBlobService{id: {BlobServiceId}})
#     ON CREATE SET bs.firstseen = timestamp(), bs.lastupdated = {azure_update_tag}
#     SET bs.name = {Name},
#     bs.type = {Type}
#     WITH bs
#     MATCH (s:AzureStorageAccount{id: {StorageAccountId}})
#     MERGE (s)-[r:USES]->(bs)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for service in blob_services:
#         neo4j_session.run(
#             ingest_blob_services,
#             BlobServiceId=service['id'],
#             Name=service['name'],
#             Type=service['type'],
#             StorageAccountId=service['storage_account_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def sync_queue_services_details(neo4j_session, credentials, subscription_id, queue_services, update_tag):
#     queue_services_details = get_queue_services_details(credentials, subscription_id, queue_services)
#     load_queue_services_details(neo4j_session, queue_services_details, update_tag)
#
#
# @timeit
# def get_queue_services_details(credentials, subscription_id, queue_services):
#     for queue_service in queue_services:
#         queues = get_queues(credentials, subscription_id, queue_service)
#         yield queue_service['id'], queues
#
#
# @timeit
# def get_queues(credentials, subscription_id, queue_service):
#     try:
#         client = get_client(credentials, subscription_id)
#         queues = list(map(lambda x: x.as_dict(), client.queue.list(queue_service['resource_group_name'], queue_service['storage_account_name'])))
#
#     except Exception as e:
#         logger.warning("Error while retrieving queues - {}".format(e))
#         return []
#
#     return queues
#
#
# @timeit
# def load_queue_services_details(neo4j_session, details, update_tag):
#     queues = []
#
#     for queue_service_id, queue in details:
#         if len(queue) > 0:
#             for q in queue:
#                 q['service_id'] = queue_service_id
#             queues.extend(queue)
#
#     _load_queues(neo4j_session, queues, update_tag)
#
#
# @timeit
# def _load_queues(neo4j_session, queues, update_tag):
#     ingest_queues = """
#     MERGE (q:AzureStorageQueue{id: {QueueId}})
#     ON CREATE SET q.firstseen = timestamp(), q.lastupdated = {azure_update_tag}
#     SET q.name = {Name},
#     q.type = {Type}
#     WITH q
#     MATCH (qs:AzureStorageQueueService{id: {ServiceId}})
#     MERGE (qs)-[r:CONTAINS]->(q)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for queue in queues:
#         neo4j_session.run(
#             ingest_queues,
#             QueueId=queue['id'],
#             Name=queue['name'],
#             Type=queue['type'],
#             ServiceId=queue['service_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def sync_table_services_details(neo4j_session, credentials, subscription_id, table_services, update_tag):
#     table_services_details = get_table_services_details(credentials, subscription_id, table_services)
#     load_table_services_details(neo4j_session, table_services_details, update_tag)
#
#
# @timeit
# def get_table_services_details(credentials, subscription_id, table_services):
#     for table_service in table_services:
#         tables = get_tables(credentials, subscription_id, table_service)
#         yield table_service['id'], tables
#
#
# @timeit
# def get_tables(credentials, subscription_id, table_service):
#     try:
#         client = get_client(credentials, subscription_id)
#         tables = list(map(lambda x: x.as_dict(), client.table.list(table_service['resource_group_name'], table_service['storage_account_name'])))
#
#     except Exception as e:
#         logger.warning("Error while retrieving tables - {}".format(e))
#         return []
#
#     return tables
#
#
# @timeit
# def load_table_services_details(neo4j_session, details, update_tag):
#     tables = []
#
#     for table_service_id, table in details:
#         if len(table) > 0:
#             for t in table:
#                 t['service_id'] = table_service_id
#             tables.extend(table)
#
#     _load_tables(neo4j_session, tables, update_tag)
#
#
# @timeit
# def _load_tables(neo4j_session, tables, update_tag):
#     ingest_tables = """
#     MERGE (t:AzureStorageTable{id: {TableId}})
#     ON CREATE SET t.firstseen = timestamp(), t.lastupdated = {azure_update_tag}
#     SET t.name = {Name},
#     t.type = {Type},
#     t.tablename = {TableName}
#     WITH t
#     MATCH (ts:AzureStorageTableService{id: {ServiceId}})
#     MERGE (ts)-[r:CONTAINS]->(t)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for table in tables:
#         neo4j_session.run(
#             ingest_tables,
#             TableId=table['id'],
#             Name=table['name'],
#             Type=table['type'],
#             TableName=table['properties']['tableName'],
#             ServiceId=table['service_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def sync_file_services_details(neo4j_session, credentials, subscription_id, file_services, update_tag):
#     file_services_details = get_file_services_details(credentials, subscription_id, file_services)
#     load_file_services_details(neo4j_session, file_services_details, update_tag)
#
#
# @timeit
# def get_file_services_details(credentials, subscription_id, file_services):
#     for file_service in file_services:
#         shares = get_shares(credentials, subscription_id, file_service)
#         yield file_service['id'], shares
#
#
# @timeit
# def get_shares(credentials, subscription_id, file_service):
#     try:
#         client = get_client(credentials, subscription_id)
#         shares = list(map(lambda x: x.as_dict(), client.file_shares.list(file_service['resource_group_name'], file_service['storage_account_name'])))
#
#     except Exception as e:
#         logger.warning("Error while retrieving file shares - {}".format(e))
#         return []
#
#     return shares
#
#
# @timeit
# def load_file_services_details(neo4j_session, details, update_tag):
#     shares = []
#
#     for file_service_id, share in details:
#         if len(share) > 0:
#             for s in share:
#                 s['service_id'] = file_service_id
#             shares.extend(share)
#
#     _load_shares(neo4j_session, shares, update_tag)
#
#
# @timeit
# def _load_shares(neo4j_session, shares, update_tag):
#     ingest_shares = """
#     MERGE (share:AzureStorageFileShare{id: {ShareId}})
#     ON CREATE SET share.firstseen = timestamp(), share.lastupdated = {azure_update_tag}
#     SET share.name = {Name},
#     share.type = {Type},
#     share.tablename = {TableName},
#     share.lastmodifiedtime = {LastModifiedTime},
#     share.sharequota = {ShareQuota},
#     share.accesstier = {AccessTier},
#     share.deleted = {Deleted},
#     share.accesstierchangetime = {AccessTierChangeTime},
#     share.accesstierstatus = {AccessTierStatus},
#     share.deletedtime = {DeletedTime},
#     share.enabledProtocols = {EnabledProtocols},
#     share.remainingretentiondays = {RemainingRetentionDays},
#     share.shareusagebytes = {ShareUsageBytes},
#     share.version = {Version}
#     WITH share
#     MATCH (fs:AzureStorageFileService{id: {ServiceId}})
#     MERGE (fs)-[r:CONTAINS]->(share)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for share in shares:
#         neo4j_session.run(
#             ingest_shares,
#             ShareId=share['id'],
#             Name=share['name'],
#             Type=share['type'],
#             LastModifiedTime=share['properties']['lastModifiedTime'],
#             ShareQuota=share['properties']['shareQuota'],
#             AccessTier=share['properties']['accessTier'],
#             Deleted=share['properties']['deleted'],
#             AccessTierChangeTime=share['properties']['accessTierChangeTime'],
#             AccessTierStatus=share['properties']['accessTierStatus'],
#             DeletedTime=share['properties']['deletedTime'],
#             EnabledProtocols=share['properties']['enabledProtocols'],
#             RemainingRetentionDays=share['properties']['remainingRetentionDays'],
#             ShareUsageBytes=share['properties']['shareUsageBytes'],
#             Version=share['properties']['version'],
#             ServiceId=share['service_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def sync_blob_services_details(neo4j_session, credentials, subscription_id, blob_services, update_tag):
#     blob_services_details = get_blob_services_details(credentials, subscription_id, blob_services)
#     load_blob_services_details(neo4j_session, blob_services_details, update_tag)
#
#
# @timeit
# def get_blob_services_details(credentials, subscription_id, blob_services):
#     for blob_service in blob_services:
#         blob_containers = get_blob_containers(credentials, subscription_id, blob_service)
#         yield blob_service['id'], blob_containers
#
#
# @timeit
# def get_blob_containers(credentials, subscription_id, blob_service):
#     try:
#         client = get_client(credentials, subscription_id)
#         blob_containers = list(map(lambda x: x.as_dict(), client.blob_containers.list(blob_service['resource_group_name'], blob_service['storage_account_name'])))
#
#     except Exception as e:
#         logger.warning("Error while retrieving blob_containers - {}".format(e))
#         return []
#
#     return blob_containers
#
#
# @timeit
# def load_blob_services_details(neo4j_session, details, update_tag):
#     blob_containers = []
#
#     for blob_service_id, container in details:
#         if len(container) > 0:
#             for c in container:
#                 c['service_id'] = blob_service_id
#             blob_containers.extend(container)
#
#     _load_blob_containers(neo4j_session, blob_containers, update_tag)
#
#
# @timeit
# def _load_blob_containers(neo4j_session, blob_containers, update_tag):
#     ingest_blob_containers = """
#     MERGE (bc:AzureStorageBlobContainer{id: {ContainerId}})
#     ON CREATE SET bc.firstseen = timestamp(), bc.lastupdated = {azure_update_tag}
#     SET bc.name = {Name},
#     bc.type = {Type},
#     bc.deleted = {Deleted},
#     bc.deletedTime = {DeletedTime},
#     bc.defaultencryptionscope = {DefaultEncryptionScope},
#     bc.publicaccess = {PublicAccess},
#     bc.leaseStatus = {LeaseStatus},
#     bc.leasestate = {LeaseState},
#     bc.lastmodifiedtime = {LastModifiedTime},
#     bc.remainingretentiondays = {RemainingRetentionDays},
#     bc.version = {Version},
#     bc.immutabilitypolicy = {HasImmutatbilityPolicy},
#     bc.haslegalhold = {HasLegalHold},
#     bc.leaseduration = {LeaseDuration}
#     WITH bc
#     MATCH (bs:AzureStorageBlobService{id: {ServiceId}})
#     MERGE (bs)-[r:CONTAINS]->(bc)
#     ON CREATE SET r.firstseen = timestamp()
#     SET r.lastupdated = {azure_update_tag}
#     """
#
#     for container in blob_containers:
#         neo4j_session.run(
#             ingest_blob_containers,
#             ContainerId=container['id'],
#             Name=container['name'],
#             Type=container['type'],
#             Deleted=container['deleted'],
#             DeletedTime=container.get('deletedTime'),
#             DefaultEncryptionScope=container['default_encryption_scope'],
#             PublicAccess=container['public_access'],
#             LeaseStatus=container['lease_status'],
#             LeaseState=container['lease_state'],
#             LastModifiedTime=container['last_modified_time'],
#             RemainingRetentionDays=container['remaining_retention_days'],
#             Version=container.get('version'),
#             HasImmutabilityPolicy=container['has_immutability_policy'],
#             HasLegalHold=container['has_legal_hold'],
#             LeaseDuration=container.get('leaseDuration'),
#             ServiceId=container['service_id'],
#             azure_update_tag=update_tag,
#         )
#
#
# @timeit
# def cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters):
#     common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
#     run_cleanup_job('azure_storage_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure CosmosDB for subscription '%s'.", subscription_id)
    database_account_list = get_database_account_list(credentials, subscription_id)
    load_database_account_data(neo4j_session, subscription_id, database_account_list, sync_tag)
    # sync_storage_account_details(neo4j_session, credentials, subscription_id, storage_account_list, sync_tag)
    # cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters)

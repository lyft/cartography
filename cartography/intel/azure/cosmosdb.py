import logging
import uuid
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from cartography.util import get_optional_value
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
    MATCH (owner:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
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
        run_cleanup_job(
            'azure_cosmosdb_cors_details.json',
            neo4j_session,
            {'UPDATE_TAG': azure_update_tag, 'AZURE_SUBSCRIPTION_ID': subscription_id},
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


@timeit
def sync_database_account_details(neo4j_session, credentials, subscription_id, database_account_list, sync_tag):
    details = get_database_account_details(credentials, subscription_id, database_account_list)
    load_database_account_details(neo4j_session, credentials, subscription_id, details, sync_tag)


@timeit
def get_database_account_details(credentials, subscription_id, database_account_list):
    """
    Iterate over the database accounts and return the list of SQL and MongoDB databases, Cassandra keyspaces and table resources associated with each database account.
    """
    for database_account in database_account_list:
        sql_databases = get_sql_databases(credentials, subscription_id, database_account)
        cassandra_keyspaces = get_cassandra_keyspaces(credentials, subscription_id, database_account)
        mongodb_databases = get_mongodb_databases(credentials, subscription_id, database_account)
        table_resources = get_table_resources(credentials, subscription_id, database_account)
        yield database_account['id'], database_account['name'], database_account['resourceGroup'], sql_databases, cassandra_keyspaces, mongodb_databases, table_resources


@timeit
def get_sql_databases(credentials, subscription_id, database_account):
    """
    Return the list of SQL Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Check the below line of code
        sql_database_list = client.sql_resources.list_sql_databases(database_account['resourceGroup'], database_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving SQL Database list - {}".format(e))
        return []

    return sql_database_list


@timeit
def get_cassandra_keyspaces(credentials, subscription_id, database_account):
    """
    Return the list of Cassandra Keyspaces in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Check the below line of code
        cassandra_keyspace_list = client.cassandra_resources.list_cassandra_keyspaces(database_account['resourceGroup'], database_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving Cassandra keyspaces list - {}".format(e))
        return []

    return cassandra_keyspace_list


@timeit
def get_mongodb_databases(credentials, subscription_id, database_account):
    """
    Return the list of MongoDB Databases in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Check the below line of code
        mongodb_database_list = client.mongo_db_resources.list_mongo_db_databases(database_account['resourceGroup'], database_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving MongoDB Database list - {}".format(e))
        return []

    return mongodb_database_list


@timeit
def get_table_resources(credentials, subscription_id, database_account):
    """
    Return the list of Table Resources in a database account.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Check the below line of code
        table_resources_list = client.table_resources.list_tables(database_account['resourceGroup'], database_account['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving table resources list - {}".format(e))
        return []

    return table_resources_list


@timeit
def load_database_account_details(neo4j_session, credentials, subscription_id, details, update_tag):
    """
    Create dictionaries for SQL Databases, Cassandra Keyspaces, MongoDB Databases and table resources.
    """
    sql_databases = []
    cassandra_keyspaces = []
    mongodb_databases = []
    table_resources = []

    for account_id, name, resourceGroup, sql_database, cassandra_keyspace, mongodb_database, table in details:
        if len(sql_database) > 0:
            for db in sql_database:
                db['database_account_name'] = name
                db['database_account_id'] = account_id
                db['resource_group_name'] = resourceGroup
            sql_databases.extend(sql_database)

        if len(cassandra_keyspace) > 0:
            for keyspace in cassandra_keyspace:
                keyspace['database_account_name'] = name
                keyspace['database_account_id'] = account_id
                keyspace['resource_group_name'] = resourceGroup
            cassandra_keyspaces.extend(cassandra_keyspace)

        if len(mongodb_database) > 0:
            for db in mongodb_database:
                db['database_account_name'] = name
                db['database_account_id'] = account_id
                db['resource_group_name'] = resourceGroup
            mongodb_databases.extend(mongodb_database)

        if len(table) > 0:
            for t in table:
                t['database_account_id'] = account_id
            table_resources.extend(table)

    _load_sql_databases(neo4j_session, sql_databases, update_tag)
    _load_cassandra_keyspaces(neo4j_session, cassandra_keyspaces, update_tag)
    _load_mongodb_databases(neo4j_session, mongodb_databases, update_tag)
    _load_table_resources(neo4j_session, table_resources, update_tag)

    sync_sql_database_details(neo4j_session, credentials, subscription_id, sql_databases, update_tag)
    sync_cassandra_keyspace_details(neo4j_session, credentials, subscription_id, cassandra_keyspaces, update_tag)
    sync_mongodb_database_details(neo4j_session, credentials, subscription_id, mongodb_databases, update_tag)


@timeit
def _load_sql_databases(neo4j_session, sql_databases, update_tag):
    """
    Ingest SQL Databases into neo4j.
    """
    ingest_sql_databases = """
    MERGE (sdb:AzureCosmosDBSqlDatabase{id: {SQLDatabaseId}})
    ON CREATE SET sdb.firstseen = timestamp(), sdb.lastupdated = {azure_update_tag}
    SET sdb.name = {Name},
    sdb.type = {Type},
    sdb.location = {Location},
    sdb.throughput = {Throughput},
    sdb.maxthroughput = {MaxThroughput}
    WITH sdb
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(sdb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for database in sql_databases:
        neo4j_session.run(
            ingest_sql_databases,
            SQLDatabaseId=database['id'],
            Name=database['name'],
            Type=database['type'],
            Location=database['location'],
            Throughput=database['options']['throughput'],
            MaxThroughput=database['options']['autoscale_setting']['max_throughput'],
            DatabaseAccountId=database['database_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_cassandra_keyspaces(neo4j_session, cassandra_keyspaces, update_tag):
    """
    Ingest Cassandra keyspaces into neo4j.
    """
    ingest_cassandra_keyspaces = """
    MERGE (ck:AzureCosmosDBCassandraKeyspace{id: {KeyspaceId}})
    ON CREATE SET ck.firstseen = timestamp(), ck.lastupdated = {azure_update_tag}
    SET ck.name = {Name},
    ck.type = {Type},
    ck.location = {Location},
    ck.throughput = {Throughput},
    ck.maxthroughput = {MaxThroughput}
    WITH ck
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(ck)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for keyspace in cassandra_keyspaces:
        neo4j_session.run(
            ingest_cassandra_keyspaces,
            KeyspaceId=keyspace['id'],
            Name=keyspace['name'],
            Type=keyspace['type'],
            Location=keyspace['location'],
            Throughput=keyspace['options']['throughput'],
            MaxThroughput=keyspace['options']['autoscale_setting']['max_throughput'],
            DatabaseAccountId=keyspace['database_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_mongodb_databases(neo4j_session, mongodb_databases, update_tag):
    """
    Ingest MongoDB databases into neo4j.
    """
    ingest_mongodb_databases = """
    MERGE (mdb:AzureCosmosDBMongoDBDatabase{id: {DatabaseId}})
    ON CREATE SET mdb.firstseen = timestamp(), mdb.lastupdated = {azure_update_tag}
    SET mdb.name = {Name},
    mdb.type = {Type},
    mdb.location = {Location},
    mdb.throughput = {Throughput},
    mdb.maxthroughput = {MaxThroughput}
    WITH mdb
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(mdb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for database in mongodb_databases:
        neo4j_session.run(
            ingest_mongodb_databases,
            DatabaseId=database['id'],
            Name=database['name'],
            Type=database['type'],
            Location=database['location'],
            Throughput=database['options']['throughput'],
            MaxThroughput=database['options']['autoscale_setting']['max_throughput'],
            DatabaseAccountId=database['database_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_table_resources(neo4j_session, table_resources, update_tag):
    """
    Ingest Table resources into neo4j.
    """
    ingest_tables = """
    MERGE (tr:AzureCosmosDBTableResource{id: {ResourceId}})
    ON CREATE SET tr.firstseen = timestamp(), tr.lastupdated = {azure_update_tag}
    SET tr.name = {Name},
    tr.type = {Type},
    tr.location = {Location},
    tr.throughput = {Throughput},
    tr.maxthroughput = {MaxThroughput}
    WITH tr
    MATCH (d:AzureDatabaseAccount{id: {DatabaseAccountId}})
    MERGE (d)-[r:CONTAINS]->(tr)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for table in table_resources:
        neo4j_session.run(
            ingest_tables,
            ResourceId=table['id'],
            Name=table['name'],
            Type=table['type'],
            Location=table['location'],
            Throughput=table['options']['throughput'],
            MaxThroughput=table['options']['autoscale_setting']['max_throughput'],
            DatabaseAccountId=table['database_account_id'],
            azure_update_tag=update_tag,
        )


@timeit
def sync_sql_database_details(neo4j_session, credentials, subscription_id, sql_databases, update_tag):
    sql_database_details = get_sql_database_details(credentials, subscription_id, sql_databases)
    load_sql_database_details(neo4j_session, sql_database_details, update_tag)


@timeit
def get_sql_database_details(credentials, subscription_id, sql_databases):
    """
    Iterate over the SQL databases to retrieve the SQL containers in them.
    """
    for database in sql_databases:
        containers = get_sql_containers(credentials, subscription_id, database)
        yield database['id'], containers


@timeit
def get_sql_containers(credentials, subscription_id, database):
    """
    Returns the list of SQL containers in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO : test this below line of code
        containers = list(map(lambda x: x.as_dict(), client.sql_resources.list_sql_containers(database['resource_group_name'], database['database_account_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving SQL Containers - {}".format(e))
        return []

    return containers


@timeit
def load_sql_database_details(neo4j_session, details, update_tag):
    """
    Create dictionary for SQL Containers
    """
    containers = []

    for database_id, container in details:
        if len(container) > 0:
            for c in container:
                c['database_id'] = database_id
            containers.extend(container)

    _load_sql_containers(neo4j_session, containers, update_tag)


@timeit
def _load_sql_containers(neo4j_session, containers, update_tag):
    """
    Ingest SQL Container details into neo4j.
    """
    ingest_containers = """
    MERGE (c:AzureCosmosDBSqlContainer{id: {ResourceId}})
    ON CREATE SET c.firstseen = timestamp(), c.lastupdated = {azure_update_tag}
    SET c.name = {Name},
    c.type = {Type},
    c.location = {Location},
    c.throughput = {Throughput},
    c.maxthroughput = {MaxThroughput},
    c.container = {ContainerId},
    c.defaultttl = {DefaultTimeToLive},
    c.analyticalttl = {AnalyticalTTL},
    c.isautomaticindexingpolicy = {IsAutomaticIndexingPolicy},
    c.indexingmode = {IndexingMode},
    c.conflictresolutionpolicymode = {ConflictResolutionPolicyMode}
    WITH c
    MATCH (sdb:AzureCosmosDBSqlDatabase{id: {SQLDatabaseId}})
    MERGE (sdb)-[r:CONTAINS]->(c)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for container in containers:
        neo4j_session.run(
            ingest_containers,
            ResourceId=container['id'],
            Name=container['name'],
            Type=container['type'],
            Location=container['location'],
            Throughput=container['options']['throughput'],
            MaxThroughput=container['options']['autoscale_settings']['max_throughput'],
            ContainerId=container['resource']['id'],
            DefaultTimeToLive=container['resource']['default_ttl'],
            AnalyticalTTL=container['resource']['analytical_storage_ttl'],
            IsAutomaticIndexingPolicy=container['resource']['indexing_policy']['automatic'],
            IndexingMode=container['resource']['indexing_policy']['indexing_mode'],
            ConflictResolutionPolicyMode=container['resource']['conflict_resolution_policy']['mode'],
            SQLDatabaseId=container['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def sync_cassandra_keyspace_details(neo4j_session, credentials, subscription_id, cassandra_keyspaces, update_tag):
    cassandra_keyspace_details = get_cassandra_keyspace_details(credentials, subscription_id, cassandra_keyspaces)
    load_cassandra_keyspace_details(neo4j_session, cassandra_keyspace_details, update_tag)


@timeit
def get_cassandra_keyspace_details(credentials, subscription_id, cassandra_keyspaces):
    """
    Iterate through the Cassandra keyspaces to get the list of tables in each keyspace.
    """
    for keyspace in cassandra_keyspaces:
        tables = get_cassandra_tables(credentials, subscription_id, keyspace)
        yield keyspace['id'], tables


@timeit
def get_cassandra_tables(credentials, subscription_id, keyspace):
    """
    Returns the list of tables in a Cassandra Keyspace.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Test the below line of code
        tables = list(map(lambda x: x.as_dict(), client.cassandra_resources.list_cassandra_tables(keyspace['resource_group_name'], keyspace['database_account_name'], keyspace['name'])))

    except Exception as e:
        logger.warning("Error while retrieving Cassandra tables - {}".format(e))
        return []

    return tables


@timeit
def load_cassandra_keyspace_details(neo4j_session, details, update_tag):
    """
    Create a dictionary for Cassandra tables.
    """
    tables = []

    for keyspace_id, table in details:
        if len(table) > 0:
            for t in table:
                t['keyspace_id'] = keyspace_id
            tables.extend(table)

    _load_cassandra_tables(neo4j_session, tables, update_tag)


@timeit
def _load_cassandra_tables(neo4j_session, tables, update_tag):
    """
    Ingest Cassandra Tables into neo4j.
    """
    ingest_cassandra_tables = """
    MERGE (ct:AzureCosmosDBCassandraTable{id: {ResourceId}})
    ON CREATE SET ct.firstseen = timestamp(), ct.lastupdated = {azure_update_tag}
    SET ct.name = {Name},
    ct.type = {Type},
    ct.location = {Location},
    ct.throughput = {Throughput},
    ct.maxthroughput = {MaxThroughput},
    ct.container = {TableId},
    ct.defaultttl = {DefaultTimeToLive},
    ct.analyticalttl = {AnalyticalTTL}
    WITH ct
    MATCH (ck:AzureCosmosDBCassandraKeyspace{id: {KeyspaceId}})
    MERGE (ck)-[r:CONTAINS]->(ct)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for table in tables:
        neo4j_session.run(
            ingest_cassandra_tables,
            ResourceId=table['id'],
            Name=table['name'],
            Type=table['type'],
            Location=table['location'],
            Throughput=table['options']['throughput'],
            MaxThroughput=table['options']['autoscale_settings']['max_throughput'],
            TableId=table['resource']['id'],
            DefaultTimeToLive=table['resource']['default_ttl'],
            AnalyticalTTL=table['resource']['analytical_storage_ttl'],
            KeyspaceId=table['keyspace_id'],
            azure_update_tag=update_tag,
        )


@timeit
def sync_mongodb_database_details(neo4j_session, credentials, subscription_id, mongodb_databases, update_tag):
    mongodb_databases_details = get_mongodb_databases_details(credentials, subscription_id, mongodb_databases)
    load_mongodb_databases_details(neo4j_session, mongodb_databases_details, update_tag)


@timeit
def get_mongodb_databases_details(credentials, subscription_id, mongodb_databases):
    """
    Iterate through the MongoDB Databases to get the list of collections in each mongoDB database.
    """
    for database in mongodb_databases:
        collections = get_mongodb_collections(credentials, subscription_id, database)
        yield database['id'], collections


@timeit
def get_mongodb_collections(credentials, subscription_id, database):
    """
    Returns the list of collections in a MongoDB Database.
    """
    try:
        client = get_client(credentials, subscription_id)
        # TODO: Test the below line of code
        collections = list(map(lambda x: x.as_dict(), client.mongo_db_resources.list_mongo_db_collections(database['resource_group_name'], database['database_account_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving MongoDB collections - {}".format(e))
        return []

    return collections


@timeit
def load_mongodb_databases_details(neo4j_session, details, update_tag):
    """
    Create a dictionary for MongoDB tables.
    """
    collections = []

    for database_id, collection in details:
        if len(collection) > 0:
            for c in collection:
                c['database_id'] = database_id
            collections.extend(collection)

    _load_collections(neo4j_session, collections, update_tag)


@timeit
def _load_collections(neo4j_session, collections, update_tag):
    """
    Ingest MongoDB Collections into neo4j.
    """
    ingest_collections = """
    MERGE (col:AzureCosmosDBMongoDBCollection{id: {ResourceId}})
    ON CREATE SET col.firstseen = timestamp(), col.lastupdated = {azure_update_tag}
    SET col.name = {Name},
    col.type = {Type},
    col.location = {Location},
    col.throughput = {Throughput},
    col.maxthroughput = {MaxThroughput},
    col.collectionname = {CollectionName},
    col.analyticalttl = {AnalyticalTTL}
    WITH col
    MATCH (mdb:AzureCosmosDBMongoDBDatabase{id: {DatabaseId}})
    MERGE (mdb)-[r:CONTAINS]->(col)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for collection in collections:
        neo4j_session.run(
            ingest_collections,
            ResourceId=collection['id'],
            Name=collection['name'],
            Type=collection['type'],
            Location=collection['location'],
            Throughput=collection['options']['throughput'],
            MaxThroughput=collection['options']['autoscale_settings']['max_throughput'],
            CollectionName=collection['resource']['id'],
            AnalyticalTTL=collection['resource']['analytical_storage_ttl'],
            DatabaseId=collection['database_id'],
            azure_update_tag=update_tag,
        )


# @timeit
# def cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters):
#     common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
#     run_cleanup_job('azure_storage_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure CosmosDB for subscription '%s'.", subscription_id)
    database_account_list = get_database_account_list(credentials, subscription_id)
    load_database_account_data(neo4j_session, subscription_id, database_account_list, sync_tag)
    sync_database_account_details(neo4j_session, credentials, subscription_id, database_account_list, sync_tag)
    # cleanup_azure_storage_accounts(neo4j_session, subscription_id, common_job_parameters)

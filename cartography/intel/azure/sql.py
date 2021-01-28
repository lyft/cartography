import logging
from azure.mgmt.sql import SqlManagementClient
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(credentials, subscription_id):
    client = SqlManagementClient(credentials, subscription_id)
    return client


@timeit
def get_server_list(credentials, subscription_id):
    try:
        client = get_client(credentials, subscription_id)
        server_list = list(map(lambda x: x.as_dict(), client.servers.list()))

    except Exception as e:
        logger.warning("Error while retrieving servers - {}".format(e))
        return []

    for server in server_list:
        x = server['id'].split('/')
        server['resourceGroup'] = x[x.index('resourceGroups')+1]

    return server_list


@timeit
def load_server_data(neo4j_session, subscription_id, server_list, azure_update_tag):

    ingest_server = """
    MERGE (s:AzureServer{id: {ServerId}})
    ON CREATE SET s.firstseen = timestamp(), 
    s.id = {ServerId}, s.name = {Name}, 
    s.resourcegroup = {ResourceGroup}, s.location = {Location}
    SET s.lastupdated = {azure_update_tag}, 
    s.kind = {Kind},
    s.state = {State},
    s.version = {Version}
    WITH s
    MATCH (owner:AzureAccount{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for server in server_list:
        neo4j_session.run(
            ingest_server,
            ServerId=server['id'],
            ResourceGroup=server['resourceGroup'],
            Name=server['name'],
            Location=server['location'],
            Kind=server['kind'],
            State=server['properties']['state'],
            Version=server['properties']['version'],
            AZURE_SUBSCRIPTION_ID=subscription_id,
            azure_update_tag=azure_update_tag,
        )


@timeit
def sync_server_details(neo4j_session, credentials, subscription_id, server_list, sync_tag):
    details = get_server_details(credentials, subscription_id, server_list)
    load_server_details(neo4j_session, credentials, subscription_id, details, sync_tag)


@timeit
def get_server_details(credentials, subscription_id, server_list):
    for server in server_list:
        dns_alias = get_dns_aliases(credentials, subscription_id, server)
        ad_admins = get_ad_admins(credentials, subscription_id, server)
        recoverable_databases = get_recoverable_databases(credentials, subscription_id, server)
        restorable_dropped_databases = get_restorable_dropped_databases(credentials, subscription_id, server)
        failover_groups = get_failover_groups(credentials, subscription_id, server)
        elastic_pools = get_elastic_pools(credentials, subscription_id, server)
        databases = get_databases(credentials, subscription_id, server)
        yield server['id'], server['name'], server['resourceGroup'], dns_alias, ad_admins, recoverable_databases, restorable_dropped_databases, failover_groups, elastic_pools, databases


@timeit
def get_dns_aliases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        dns_aliases = client.server_dns_aliases.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving Azure Server DNS Aliases - {}".format(e))
        return []

    return dns_aliases


@timeit
def get_ad_admins(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        ad_admins = client.server_azure_ad_administrators.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving server azure AD Administrators - {}".format(e))
        return []

    return ad_admins


@timeit
def get_recoverable_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        recoverable_databases = client.recoverable_databases.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving recoverable databases - {}".format(e))
        return []

    return recoverable_databases


@timeit
def get_restorable_dropped_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        restorable_dropped_databases = client.restorable_dropped_databases.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving restorable dropped databases - {}".format(e))
        return []

    return restorable_dropped_databases


@timeit
def get_failover_groups(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        failover_groups = client.failover_groups.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving failover groups - {}".format(e))
        return []

    return failover_groups


@timeit
def get_elastic_pools(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        elastic_pools = client.elastic_pools.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving elastic pools - {}".format(e))
        return []

    return elastic_pools


@timeit
def get_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        databases = client.databases.list_by_server(server['resourceGroup'], server['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving databases - {}".format(e))
        return []

    return databases


@timeit
def load_server_details(neo4j_session, credentials, subscription_id, details, update_tag):
    dns_aliases = []
    ad_admins = []
    recoverable_databases = []
    restorable_dropped_databases = []
    failover_groups = []
    elastic_pools = []
    databases = []

    for server_id, name, resourceGroup, dns_alias, ad_admin, r_database, rd_database, failover_group, elastic_pool, database in details:
        if len(dns_alias) > 0:
            for alias in dns_alias:
                alias['server_name'] = name
                alias['server_id'] = server_id
                dns_aliases.extend(alias)

        if len(ad_admin) > 0:
            for admin in ad_admin:
                admin['server_name'] = name
                admin['server_id'] = server_id
                ad_admins.extend(admin)

        if len(r_database) > 0:
            for rdb in r_database:
                rdb['server_name'] = name
                rdb['server_id'] = server_id
                recoverable_databases.extend(rdb)

        if len(rd_database) > 0:
            for rddb in rd_database:
                rddb['server_name'] = name
                rddb['server_id'] = server_id
                restorable_dropped_databases.extend(rddb)

        if len(failover_group) > 0:
            for group in failover_group:
                group['server_name'] = name
                group['server_id'] = server_id
                failover_groups.extend(group)

        if len(elastic_pool) > 0:
            for pool in elastic_pool:
                pool['server_name'] = name
                pool['server_id'] = server_id
                elastic_pools.extend(pool)

        if len(database) > 0:
            for db in database:
                db['server_name'] = name
                db['server_id'] = server_id
                db['resource_group_name'] = resourceGroup
                databases.extend(db)

    _load_server_dns_aliases(neo4j_session, dns_aliases, update_tag)
    _load_server_ad_admins(neo4j_session, ad_admins, update_tag)
    _load_recoverable_databases(neo4j_session, recoverable_databases, update_tag)
    _load_restorable_dropped_databases(neo4j_session, restorable_dropped_databases, update_tag)
    _load_failover_groups(neo4j_session, failover_groups, update_tag)
    _load_elastic_pools(neo4j_session, elastic_pools, update_tag)
    _load_databases(neo4j_session, databases, update_tag)

    sync_database_details(neo4j_session, credentials, subscription_id, databases, update_tag)


@timeit
def _load_server_dns_aliases(neo4j_session, dns_aliases, update_tag):
    ingest_dns_aliases = """
    MERGE (alias:AzureServerDNSAlias{id: {DNSAliasId}})
    ON CREATE SET alias.firstseen = timestamp(), alias.lastupdated = {azure_update_tag}
    SET alias.name = {Name},
    alias.dnsrecord = {AzureDNSRecord}
    WITH alias
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:USED_BY]->(alias)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for data in dns_aliases:
        neo4j_session.run(
            ingest_dns_aliases,
            DNSAliasId=data['id'],
            Name=data['name'],
            AzureDNSRecord=data['properties']['azureDnsRecord'],
            ServerId=data['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_server_ad_admins(neo4j_session, ad_admins, update_tag):
    ingest_ad_admins = """
    MERGE (a:AzureServerADAdministrator{id: {AdAdminId}})
    ON CREATE SET a.firstseen = timestamp(), a.lastupdated = {azure_update_tag}
    SET a.name = {Name},
    a.type = {AdministratorType},
    a.login = {Login}
    WITH a
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:ADMINISTERED_BY]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for data in ad_admins:
        neo4j_session.run(
            ingest_ad_admins,
            AdAdminId=data['id'],
            Name=data['name'],
            AdministratorType=data['properties']['administratorType'],
            Login=data['properties']['login'],
            ServerId=data['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_recoverable_databases(neo4j_session, recoverable_databases, update_tag):
    ingest_recoverable_databases = """
    MERGE (rd:AzureRecoverableDatabase{id: {DatabaseId}})
    ON CREATE SET rd.firstseen = timestamp(), rd.lastupdated = {azure_update_tag}
    SET rd.name = {Name},
    rd.edition = {Edition},
    rd.servicelevelobjective = {ServiceLevelObjective},
    rd.lastbackupdate = {BackupDate}
    WITH rd
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:RESOURCE]->(rd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for data in recoverable_databases:
        neo4j_session.run(
            ingest_recoverable_databases,
            DatabaseId=data['id'],
            Name=data['name'],
            Edition=data['properties']['edition'],
            ServiceLevelObjective=data['properties']['serviceLevelObjective'],
            BackupDate=data['properties']['lastAvailableBackupDate'],
            ServerId=data['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_restorable_dropped_databases(neo4j_session, restorable_dropped_databases, update_tag):
    ingest_restorable_dropped_databases = """
    MERGE (rdd:AzureRestorableDroppedDatabase{id: {DatabaseId}})
    ON CREATE SET rdd.firstseen = timestamp(), rdd.lastupdated = {azure_update_tag}
    SET rdd.name = {Name},
    rdd.location = {Location},
    rdd.databasename = {DatabaseName},
    rdd.creationdate = {CreationDate},
    rdd.deletiondate = {DeletionDate},
    rdd.restoredate = {RestoreDate},
    rdd.edition = {Edition},
    rdd.servicelevelobjective = {ServiceLevelObjective},
    rdd.maxsizebytes = {MaxSizeBytes}
    WITH rdd
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:RESOURCE]->(rdd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for data in restorable_dropped_databases:
        neo4j_session.run(
            ingest_restorable_dropped_databases,
            DatabaseId=data['id'],
            Name=data['name'],
            Location=data['location'],
            DatabaseName=data['properties']['databaseName'],
            CreationDate=data['properties']['creationDate'],
            DeletionDate=data['properties']['deletionDate'],
            RestoreDate=data['properties']['earliestRestoreDate'],
            Edition=data['properties']['edition'],
            ServiceLevelObjective=data['properties']['serviceLevelObjective'],
            MaxSizeBytes=data['properties']['maxSizeBytes'],
            ServerId=data['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_failover_groups(neo4j_session, failover_groups, update_tag):
    ingest_failover_groups = """
    MERGE (f:AzureFailoverGroup{id: {GroupId}})
    ON CREATE SET f.firstseen = timestamp(), f.lastupdated = {azure_update_tag}
    SET f.name = {Name},
    f.location = {Location},
    f.replicationrole = {Role},
    f.replicationstate = {State}
    WITH f
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:RESOURCE]->(f)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for group in failover_groups:
        neo4j_session.run(
            ingest_failover_groups,
            GroupId=group['id'],
            Name=group['name'],
            Location=group['location'],
            Role=group['properties']['replicationRole'],
            State=group['properties']['replicationState'],
            ServerId=group['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_elastic_pools(neo4j_session, elastic_pools, update_tag):
    ingest_elastic_pools = """
    MERGE (e:AzureElasticPool{id: {PoolId}})
    ON CREATE SET e.firstseen = timestamp(), e.lastupdated = {azure_update_tag}
    SET e.name = {Name},
    e.location = {Location},
    e.creationdate = {CreationDate},
    e.state = {State},
    e.maxsizebytes = {MaxSizeBytes},
    e.licensetype = {LicenseType},
    e.zoneredundant = {ZoneRedundant}
    WITH e
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for elastic_pool in elastic_pools:
        neo4j_session.run(
            ingest_elastic_pools,
            PoolId=elastic_pool['id'],
            Name=elastic_pool['name'],
            Location=elastic_pool['location'],
            CreationDate=elastic_pool['properties']['creationDate'],
            State=elastic_pool['properties']['state'],
            MaxSizeBytes=elastic_pool['properties']['maxSizeBytes'],
            LicenseType=elastic_pool['properties']['licenseType'],
            ZoneRedundant=elastic_pool['properties']['zoneRedundant'],
            ServerId=elastic_pool['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_databases(neo4j_session, databases, update_tag):
    ingest_databases = """
    MERGE (d:AzureDatabase{id: {Id}})
    ON CREATE SET d.firstseen = timestamp(), d.lastupdated = {azure_update_tag}
    SET d.name = {Name},
    d.location = {Location},
    d.kind = {Kind},
    d.creationdate = {CreationDate},
    d.databaseid = {DatabaseId},
    d.maxsizebytes = {MaxSizeBytes},
    d.licensetype = {LicenseType},
    d.secondarylocation = {SecondaryLocation},
    d.elasticpoolid = {ElasticPoolId},
    d.collation = {Collation},
    d.failovergroupid = {FailoverGroupId},
    d.restorabledroppeddbid = {RDDId},
    d.recoverabledbid = {RecoverableDbId}
    WITH d
    MATCH (s:AzureServer{id: {ServerId}})
    MERGE (s)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for database in databases:
        neo4j_session.run(
            ingest_databases,
            Id=database['id'],
            Name=database['name'],
            Location=database['location'],
            Kind=database['kind'],
            CreationDate=database['properties']['creationDate'],
            DatabaseId=database['properties']['databaseId'],
            MaxSizeBytes=database['properties']['maxSizeBytes'],
            LicenseType=database['properties']['licenseType'],
            SecondaryLocation=database['properties']['defaultSecondaryLocation'],
            ElasticPoolId=database['properties']['elasticPoolId'],
            Collation=database['properties']['collation'],
            FailoverGroupId=database['properties']['failoverGroupId'],
            RDDId=database['properties']['restorableDroppedDatabaseId'],
            RecoverableDbId=database['properties']['recoverableDatabaseId'],
            ServerId=database['server_id'],
            azure_update_tag=update_tag,
        )


@timeit
def sync_database_details(neo4j_session, credentials, subscription_id, databases, update_tag):
    db_details = get_database_details(credentials, subscription_id, databases)
    load_database_details(neo4j_session, db_details, update_tag)


@timeit
def get_database_details(credentials, subscription_id, databases):
    for database in databases:
        replication_links_list = get_replication_links(credentials, subscription_id, database)
        db_threat_detection_policies = get_db_threat_detection_policies(credentials, subscription_id, database)
        restore_points_list = get_restore_points(credentials, subscription_id, database)
        transparent_data_encryptions = get_transparent_data_encryptions(credentials, subscription_id, database)
        yield database['id'], replication_links_list, db_threat_detection_policies, restore_points_list, transparent_data_encryptions


@timeit
def get_replication_links(credentials, subscription_id, database):
    try:
        client = get_client(credentials, subscription_id)
        replication_links = client.replication_links.list_by_database(database['resource_group_name'], database['server_name'], database['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving replication links - {}".format(e))
        return []

    return replication_links


@timeit
def get_db_threat_detection_policies(credentials, subscription_id, database):
    try:
        client = get_client(credentials, subscription_id)
        db_threat_detection_policies = client.database_threat_detection_policies.get(database['resource_group_name'], database['server_name'], database['name'], 'default')
    except Exception as e:
        logger.warning("Error while retrieving database threat detection policies - {}".format(e))
        return []

    return db_threat_detection_policies


@timeit
def get_restore_points(credentials, subscription_id, database):
    try:
        client = get_client(credentials, subscription_id)
        restore_points_list = client.restore_points.list_by_database(database['resource_group_name'], database['server_name'], database['name']).as_dict()['value']

    except Exception as e:
        logger.warning("Error while retrieving restore points - {}".format(e))
        return []

    return restore_points_list


@timeit
def get_transparent_data_encryptions(credentials, subscription_id, database):
    try:
        client = get_client(credentials, subscription_id)
        transparent_data_encryptions_list = client.transparent_data_encryptions.get(database['resource_group_name'], database['server_name'], database['name'], 'current')
    except Exception as e:
        logger.warning("Error while retrieving transparent data encryptions - {}".format(e))
        return []

    return transparent_data_encryptions_list


@timeit
def load_database_details(neo4j_session, details, update_tag):
    replication_links = []
    threat_detection_policies = []
    restore_points = []
    encryptions_list = []

    for databaseId, replication_link, db_threat_detection_policy, restore_point, transparent_data_encryption in details:
        if len(replication_link) > 0:
            for link in replication_link:
                link['database_id'] = databaseId
                replication_links.extend(link)

        if len(db_threat_detection_policy) > 0:
            db_threat_detection_policy['database_id'] = databaseId
            threat_detection_policies.extend(db_threat_detection_policy)

        if len(restore_point) > 0:
            for point in restore_point:
                point['database_id'] = databaseId
                restore_points.extend(point)

        if len(transparent_data_encryption) > 0:
            transparent_data_encryption['database_id'] = databaseId
            encryptions_list.extend(transparent_data_encryption)

    _load_replication_links(neo4j_session, replication_links, update_tag)
    _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag)
    _load_restore_points(neo4j_session, restore_points, update_tag)
    _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag)


@timeit
def _load_replication_links(neo4j_session, replication_links, update_tag):
    ingest_replication_links = """
    MERGE (rl:AzureReplicationLink{id: {LinkId}})
    ON CREATE SET rl.firstseen = timestamp(), rl.lastupdated = {azure_update_tag}
    SET rl.name = {Name},
    rl.location = {Location},
    rl.partnerdatabase = {PartnerDatabase},
    rl.partnerlocation = {PartnerLocation},
    rl.partnerrole = {PartnerRole},
    rl.partnerserver = {PartnerServer},
    rl.mode = {Mode},
    rl.state = {State},
    rl.percentcomplete = {PercentComplete},
    rl.role = {Role},
    rl.starttime = {StartTime},
    rl.terminationallowed ={IsTerminationAllowed}
    WITH rl
    MATCH (d:AzureDatabase{id: {DatabaseId}})
    MERGE (d)-[r:CONTAINS]->(rl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for data in replication_links:
        neo4j_session.run(
            ingest_replication_links,
            LinkId=data['id'],
            Name=data['name'],
            Location=data['location'],
            PartnerDatabase=data['properties']['partnerDatabase'],
            PartnerLocation=data['properties']['partnerLocation'],
            PartnerRole=data['properties']['partnerRole'],
            PartnerServer=data['properties']['partnerServer'],
            Mode=data['properties']['replicationMode'],
            State=data['properties']['replicationState'],
            PercentComplete=data['properties']['percentComplete'],
            Role=data['properties']['role'],
            StartTime=data['properties']['startTime'],
            IsTerminationAllowed=data['properties']['isTerminationAllowed'],
            DatabaseId=data['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag):
    ingest_threat_detection_policies = """
    MERGE (policy:AzureDatabaseThreatDetectionPolicy{id: {PolicyId}})
    ON CREATE SET policy.firstseen = timestamp(), policy.lastupdated = {azure_update_tag}
    SET policy.name = {Name},
    policy.location = {Location},
    policy.kind = {Kind},
    policy.emailadmins = {EmailAdmins},
    policy.emailaddresses = {EmailAddresses},
    policy.days = {RetentionDays},
    policy.state = {State},
    policy.storageendpoint = {StorageEndpoint},
    policy.useserverdefault = {UseServerDefault},
    policy.disabledalerts = {DisabledAlerts}
    WITH policy
    MATCH (d:AzureDatabase{id: {DatabaseId}})
    MERGE (d)-[r:CONTAINS]->(policy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for policy in threat_detection_policies:
        neo4j_session.run(
            ingest_threat_detection_policies,
            PolicyId=policy['id'],
            Name=policy['name'],
            Location=policy['location'],
            Kind=policy['kind'],
            EmailAdmins=policy['properties']['emailAccountAdmins'],
            EmailAddresses=policy['properties']['emailAddresses'],
            RetentionDays=policy['properties']['retentionDays'],
            State=policy['properties']['state'],
            StorageEndpoint=policy['properties']['storageEndpoint'],
            UseServerDefault=policy['properties']['useServerDefault'],
            DisabledAlerts=policy['properties']['disabledAlerts'],
            DatabaseId=policy['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_restore_points(neo4j_session, restore_points, update_tag):
    ingest_restore_points = """
    MERGE (point:AzureRestorePoint{id: {PointId}})
    ON CREATE SET point.firstseen = timestamp(), point.lastupdated = {azure_update_tag}
    SET point.name = {Name},
    point.location = {Location},
    point.restoredate = {RestoreDate},
    point.restorepointtype = {RestorePointType},
    point.creationdate = {CreationDate}
    WITH point
    MATCH (d:AzureDatabase{id: {DatabaseId}})
    MERGE (d)-[r:CONTAINS]->(point)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for point in restore_points:
        neo4j_session.run(
            ingest_restore_points,
            PointId=point['id'],
            Name=point['name'],
            Location=point['location'],
            RestoreDate=point['properties']['earliestRestoreDate'],
            RestorePointType=point['properties']['restorePointType'],
            CreationDate=point['properties']['restorePointCreationDate'],
            DatabaseId=point['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag):
    ingest_data_encryptions = """
    MERGE (tae:AzureTransparentDataEncryption{id: {TAEId}})
    ON CREATE SET tae.firstseen = timestamp(), tae.lastupdated = {azure_update_tag}
    SET tae.name = {Name},
    tae.location = {Location},
    tae.status = {Status}
    WITH tae
    MATCH (d:AzureDatabase{id: {DatabaseId}})
    MERGE (d)-[r:CONTAINS]->(tae)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    for encryption in encryptions_list:
        neo4j_session.run(
            ingest_data_encryptions,
            TAEId=encryption['id'],
            Name=encryption['name'],
            Location=encryption['location'],
            Status=encryption['properties']['status'],
            DatabaseId=encryption['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def cleanup_azure_sql_servers(neo4j_session, subscription_id, common_job_parameters):
    common_job_parameters['AZURE_SUBSCRIPTION_ID'] = subscription_id
    run_cleanup_job('azure_sql_server_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure SQL for subscription '%s'.", subscription_id)
    server_list = get_server_list(credentials, subscription_id)
    load_server_data(neo4j_session, subscription_id, server_list, sync_tag)
    sync_server_details(neo4j_session, credentials, subscription_id, server_list, sync_tag)
    cleanup_azure_sql_servers(neo4j_session, subscription_id, common_job_parameters)

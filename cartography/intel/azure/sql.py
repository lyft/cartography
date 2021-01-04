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
        server_list = list(client.servers.list())

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
        data = server.as_dict()
        neo4j_session.run(
            ingest_server,
            ServerId=data['id'],
            ResourceGroup=data['resourceGroup'],
            Name=data['name'],
            Location=data['location'],
            Kind=data['kind'],
            State=data['properties']['state'],
            Version=data['properties']['version'],
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
        dns_aliases = list(client.server_dns_aliases.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving Azure Server DNS Aliases - {}".format(e))
        return []

    return dns_aliases


@timeit
def get_ad_admins(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        ad_admins = list(client.server_azure_ad_administrators.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving server azure AD Administrators - {}".format(e))
        return []

    return ad_admins


@timeit
def get_recoverable_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        recoverable_databases = list(client.recoverable_databases.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving recoverable databases - {}".format(e))
        return []

    return recoverable_databases


@timeit
def get_restorable_dropped_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        restorable_dropped_databases = list(client.restorable_dropped_databases.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving restorable dropped databases - {}".format(e))
        return []

    return restorable_dropped_databases


@timeit
def get_failover_groups(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        failover_groups = list(client.failover_groups.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving failover groups - {}".format(e))
        return []

    return failover_groups


@timeit
def get_elastic_pools(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        elastic_pools = list(client.elastic_pools.list_by_server(server['resourceGroup'], server['name']))

    except Exception as e:
        logger.warning("Error while retrieving elastic pools - {}".format(e))
        return []

    return elastic_pools


@timeit
def get_databases(credentials, subscription_id, server):
    try:
        client = get_client(credentials, subscription_id)
        databases = list(client.databases.list_by_server(server['resourceGroup'], server['name']))

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
            dns_alias['server_name'] = name
            dns_alias['server_id'] = server_id
            dns_aliases.extend(dns_alias)

        if len(ad_admin) > 0:
            ad_admin['server_name'] = name
            ad_admin['server_id'] = server_id
            ad_admins.extend(ad_admin)

        if len(r_database) > 0:
            r_database['server_name'] = name
            r_database['server_id'] = server_id
            recoverable_databases.extend(r_database)

        if len(rd_database) > 0:
            rd_database['server_name'] = name
            rd_database['server_id'] = server_id
            restorable_dropped_databases.extend(rd_database)

        if len(failover_group) > 0:
            failover_group['server_name'] = name
            failover_group['server_id'] = server_id
            failover_groups.extend(failover_group)

        if len(elastic_pool) > 0:
            elastic_pool['server_name'] = name
            elastic_pool['server_id'] = server_id
            elastic_pools.extend(elastic_pool)

        if len(database) > 0:
            database['server_name'] = name
            database['server_id'] = server_id
            database['resource_group_name'] = resourceGroup
            databases.extend(database)

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

    for alias in dns_aliases:
        data = alias.as_dict()
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

    for ad_admin in ad_admins:
        data = ad_admin.as_dict()
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

    for database in recoverable_databases:
        data = database.as_dict()
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

    for database in restorable_dropped_databases:
        data = database.as_dict()
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
        data = group.as_dict()
        neo4j_session.run(
            ingest_failover_groups,
            GroupId=data['id'],
            Name=data['name'],
            Location=data['location'],
            Role=data['properties']['replicationRole'],
            State=data['properties']['replicationState'],
            ServerId=data['server_id'],
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
        data = elastic_pool.as_dict()
        neo4j_session.run(
            ingest_elastic_pools,
            PoolId=data['id'],
            Name=data['name'],
            Location=data['location'],
            CreationDate=data['properties']['creationDate'],
            State=data['properties']['state'],
            MaxSizeBytes=data['properties']['maxSizeBytes'],
            LicenseType=data['properties']['licenseType'],
            ZoneRedundant=data['properties']['zoneRedundant'],
            ServerId=data['server_id'],
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
        data = database.as_dict()
        neo4j_session.run(
            ingest_databases,
            Id=data['id'],
            Name=data['name'],
            Location=data['location'],
            Kind=data['kind'],
            CreationDate=data['properties']['creationDate'],
            DatabaseId=data['properties']['databaseId'],
            MaxSizeBytes=data['properties']['maxSizeBytes'],
            LicenseType=data['properties']['licenseType'],
            SecondaryLocation=data['properties']['defaultSecondaryLocation'],
            ElasticPoolId=data['properties']['elasticPoolId'],
            Collation=data['properties']['collation'],
            FailoverGroupId=data['properties']['failoverGroupId'],
            RDDId=data['properties']['restorableDroppedDatabaseId'],
            RecoverableDbId=data['properties']['recoverableDatabaseId'],
            ServerId=data['server_id'],
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
        replication_links = list(client.replication_links.list_by_database(database['resource_group_name'], database['server_name'], database['name']))

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
        restore_points_list = list(client.restore_points.list_by_database(database['resource_group_name'], database['server_name'], database['name']))

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
            replication_link['database_id'] = databaseId
            replication_links.extend(replication_link)

        if len(db_threat_detection_policy) > 0:
            db_threat_detection_policy['database_id'] = databaseId
            threat_detection_policies.extend(db_threat_detection_policy)

        if len(restore_point) > 0:
            restore_point['database_id'] = databaseId
            restore_points.extend(restore_point)

        if len(transparent_data_encryption) > 0:
            transparent_data_encryption['database_id'] = databaseId
            encryptions_list.extend(transparent_data_encryption)

    # # cleanup existing policy properties
    # run_cleanup_job(
    #     'aws_kms_details.json',
    #     neo4j_session,
    #     {'UPDATE_TAG': update_tag, 'AWS_ID': aws_account_id},
    # )

    _load_replication_links(neo4j_session, replication_links, update_tag)
    _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag)
    _load_restore_points(neo4j_session, restore_points, update_tag)
    _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag)


@timeit
def _load_replication_links(neo4j_session, replication_links, update_tag):
    ingest_replication_links = """
    MERGE (rl:ReplicationLink{id: {LinkId}})
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

    for link in replication_links:
        data = link.as_dict()
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
    MERGE (policy:DatabaseThreatDetectionPolicy{id: {PolicyId}})
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
        data = policy.as_dict()
        neo4j_session.run(
            ingest_threat_detection_policies,
            PolicyId=data['id'],
            Name=data['name'],
            Location=data['location'],
            Kind=data['kind'],
            EmailAdmins=data['properties']['emailAccountAdmins'],
            EmailAddresses=data['properties']['emailAddresses'],
            RetentionDays=data['properties']['retentionDays'],
            State=data['properties']['state'],
            StorageEndpoint=data['properties']['storageEndpoint'],
            UseServerDefault=data['properties']['useServerDefault'],
            DisabledAlerts=data['properties']['disabledAlerts'],
            DatabaseId=data['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_restore_points(neo4j_session, restore_points, update_tag):
    ingest_restore_points = """
    MERGE (point:RestorePoint{id: {PointId}})
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
        data = point.as_dict()
        neo4j_session.run(
            ingest_restore_points,
            PointId=data['id'],
            Name=data['name'],
            Location=data['location'],
            RestoreDate=data['properties']['earliestRestoreDate'],
            RestorePointType=data['properties']['restorePointType'],
            CreationDate=data['properties']['restorePointCreationDate'],
            DatabaseId=data['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag):
    ingest_data_encryptions = """
    MERGE (tae:TransparentDataEncryption{id: {TAEId}})
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
        data = encryption.as_dict()
        neo4j_session.run(
            ingest_data_encryptions,
            TAEId=data['id'],
            Name=data['name'],
            Location=data['location'],
            Status=data['properties']['status'],
            DatabaseId=data['database_id'],
            azure_update_tag=update_tag,
        )


@timeit
def cleanup_azure_sql_servers(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_sql_server_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    logger.info("Syncing Azure SQL for subscription '%s'.", subscription_id)
    server_list = get_server_list(credentials, subscription_id)
    load_server_data(neo4j_session, subscription_id, server_list, sync_tag)
    sync_server_details(neo4j_session, credentials, subscription_id, server_list, sync_tag)
    cleanup_azure_sql_servers(neo4j_session, common_job_parameters)

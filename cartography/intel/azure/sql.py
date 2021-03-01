import logging
from azure.mgmt.sql import SqlManagementClient

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(credentials, subscription_id):
    """
    Getting the Azure SQL client
    """
    client = SqlManagementClient(credentials, subscription_id)
    return client


@timeit
def get_server_list(credentials, subscription_id):
    """
    Returning the list of servers.
    """
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
    """
    Ingest the server details into neo4j.
    """
    ingest_server = """
    UNWIND {server_list} as server
    MERGE (s:AzureServer{id: server.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.name = server.name, s.resourcegroup = server.resourceGroup,
    s.location = server.location
    SET s.lastupdated = {azure_update_tag},
    s.kind = server.kind,
    s.state = server.state,
    s.version = server.version
    WITH s
    MATCH (owner:AzureSubscription{id: {AZURE_SUBSCRIPTION_ID}})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_server,
        server_list=server_list,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )


@timeit
def sync_server_details(neo4j_session, credentials, subscription_id, server_list, sync_tag):
    details = get_server_details(credentials, subscription_id, server_list)
    load_server_details(neo4j_session, credentials, subscription_id, details, sync_tag)


@timeit
def get_server_details(credentials, subscription_id, server_list):
    """
    Iterate over each servers to get it's resource details.
    """
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
    """
    Returns details of DNS aliases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        dns_aliases = list(map(lambda x: x.as_dict(), client.server_dns_aliases.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving Azure Server DNS Aliases - {}".format(e))
        return []

    return dns_aliases


@timeit
def get_ad_admins(credentials, subscription_id, server):
    """
    Returns details of Server AD Administrators in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        ad_admins = list(map(lambda x: x.as_dict(), client.server_azure_ad_administrators.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving server azure AD Administrators - {}".format(e))
        return []

    return ad_admins


@timeit
def get_recoverable_databases(credentials, subscription_id, server):
    """
    Returns details of Recoverable databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        recoverable_databases = list(map(lambda x: x.as_dict(), client.recoverable_databases.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        if e.status_code == 404:  # The API returns a 404 Not Found Error if no recoverable databases are present.
            return []
        logger.warning("Error while retrieving recoverable databases - {}".format(e))
        return []

    return recoverable_databases


@timeit
def get_restorable_dropped_databases(credentials, subscription_id, server):
    """
    Returns details of Restorable Dropped Databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        restorable_dropped_databases = list(map(lambda x: x.as_dict(), client.restorable_dropped_databases.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving restorable dropped databases - {}".format(e))
        return []

    return restorable_dropped_databases


@timeit
def get_failover_groups(credentials, subscription_id, server):
    """
    Returns details of Failover groups in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        failover_groups = list(map(lambda x: x.as_dict(), client.failover_groups.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving failover groups - {}".format(e))
        return []

    return failover_groups


@timeit
def get_elastic_pools(credentials, subscription_id, server):
    """
    Returns details of Elastic Pools in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        elastic_pools = list(map(lambda x: x.as_dict(), client.elastic_pools.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving elastic pools - {}".format(e))
        return []

    return elastic_pools


@timeit
def get_databases(credentials, subscription_id, server):
    """
    Returns details of Databases in a server.
    """
    try:
        client = get_client(credentials, subscription_id)
        databases = list(map(lambda x: x.as_dict(), client.databases.list_by_server(server['resourceGroup'], server['name'])))

    except Exception as e:
        logger.warning("Error while retrieving databases - {}".format(e))
        return []

    return databases


@timeit
def load_server_details(neo4j_session, credentials, subscription_id, details, update_tag):
    """
    Create dictionaries for every resource in the server so we can import them in a single query
    """
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
                dns_aliases.append(alias)

        if len(ad_admin) > 0:
            for admin in ad_admin:
                admin['server_name'] = name
                admin['server_id'] = server_id
                ad_admins.append(admin)

        if len(r_database) > 0:
            for rdb in r_database:
                rdb['server_name'] = name
                rdb['server_id'] = server_id
                recoverable_databases.append(rdb)

        if len(rd_database) > 0:
            for rddb in rd_database:
                rddb['server_name'] = name
                rddb['server_id'] = server_id
                restorable_dropped_databases.append(rddb)

        if len(failover_group) > 0:
            for group in failover_group:
                group['server_name'] = name
                group['server_id'] = server_id
                failover_groups.append(group)

        if len(elastic_pool) > 0:
            for pool in elastic_pool:
                pool['server_name'] = name
                pool['server_id'] = server_id
                elastic_pools.append(pool)

        if len(database) > 0:
            for db in database:
                db['server_name'] = name
                db['server_id'] = server_id
                db['resource_group_name'] = resourceGroup
                databases.append(db)

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
    """
    Ingest the DNS Alias details into neo4j.
    """
    ingest_dns_aliases = """
    UNWIND {dns_aliases_list} as dns_alias
    MERGE (alias:AzureServerDNSAlias{id: dns_alias.id})
    ON CREATE SET alias.firstseen = timestamp(), alias.lastupdated = {azure_update_tag}
    SET alias.name = dns_alias.name,
    alias.dnsrecord = dns_alias.azure_dns_record
    WITH alias, dns_alias
    MATCH (s:AzureServer{id: dns_alias.server_id})
    MERGE (s)-[r:USED_BY]->(alias)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_dns_aliases,
        dns_aliases_list=dns_aliases,
        azure_update_tag=update_tag,
    )


@timeit
def _load_server_ad_admins(neo4j_session, ad_admins, update_tag):
    """
    Ingest the Server AD Administrators details into neo4j.
    """
    ingest_ad_admins = """
    UNWIND {ad_admins_list} as ad_admins
    MERGE (a:AzureServerADAdministrator{id: ad_admins.id})
    ON CREATE SET a.firstseen = timestamp(), a.lastupdated = {azure_update_tag}
    SET a.name = ad_admins.name,
    a.type = ad_admins.administrator_type,
    a.login = ad_admins.login
    WITH a, ad_admins
    MATCH (s:AzureServer{id: ad_admins.server_id})
    MERGE (s)-[r:ADMINISTERED_BY]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_ad_admins,
        ad_admins_list=ad_admins,
        azure_update_tag=update_tag,
    )


@timeit
def _load_recoverable_databases(neo4j_session, recoverable_databases, update_tag):
    """
    Ingest the recoverable database details into neo4j.
    """
    ingest_recoverable_databases = """
    UNWIND {recoverable_databases_list} as rec_dbs
    MERGE (rd:AzureRecoverableDatabase{id: rec_dbs.id})
    ON CREATE SET rd.firstseen = timestamp(), rd.lastupdated = {azure_update_tag}
    SET rd.name = rec_dbs.name,
    rd.edition = rec_dbs.edition,
    rd.servicelevelobjective = rec_dbs.service_level_objective,
    rd.lastbackupdate = rec_dbs.last_available_backup_date
    WITH rd, rec_dbs
    MATCH (s:AzureServer{id: rec_dbs.server_id})
    MERGE (s)-[r:RESOURCE]->(rd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_recoverable_databases,
        recoverable_databases_list=recoverable_databases,
        azure_update_tag=update_tag,
    )


@timeit
def _load_restorable_dropped_databases(neo4j_session, restorable_dropped_databases, update_tag):
    """
    Ingest the restorable dropped database details into neo4j.
    """
    ingest_restorable_dropped_databases = """
    UNWIND {restorable_dropped_databases_list} as res_dropped_dbs
    MERGE (rdd:AzureRestorableDroppedDatabase{id: res_dropped_dbs.id})
    ON CREATE SET rdd.firstseen = timestamp(), rdd.lastupdated = {azure_update_tag}
    SET rdd.name = res_dropped_dbs.name,
    rdd.location = res_dropped_dbs.location,
    rdd.databasename = res_dropped_dbs.database_name,
    rdd.creationdate = res_dropped_dbs.creation_date,
    rdd.deletiondate = res_dropped_dbs.deletion_date,
    rdd.restoredate = res_dropped_dbs.earliest_restore_date,
    rdd.edition = res_dropped_dbs.edition,
    rdd.servicelevelobjective = res_dropped_dbs.service_level_objective,
    rdd.maxsizebytes = res_dropped_dbs.max_size_bytes
    WITH rdd, res_dropped_dbs
    MATCH (s:AzureServer{id: res_dropped_dbs.server_id})
    MERGE (s)-[r:RESOURCE]->(rdd)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_restorable_dropped_databases,
        restorable_dropped_databases_list=restorable_dropped_databases,
        azure_update_tag=update_tag,
    )


@timeit
def _load_failover_groups(neo4j_session, failover_groups, update_tag):
    """
    Ingest the failover groups details into neo4j.
    """
    ingest_failover_groups = """
    UNWIND {failover_groups_list} as fg
    MERGE (f:AzureFailoverGroup{id: fg.id})
    ON CREATE SET f.firstseen = timestamp(), f.lastupdated = {azure_update_tag}
    SET f.name = fg.name,
    f.location = fg.location,
    f.replicationrole = fg.replication_role,
    f.replicationstate = fg.replication_state
    WITH f, fg
    MATCH (s:AzureServer{id: fg.server_id})
    MERGE (s)-[r:RESOURCE]->(f)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_failover_groups,
        failover_groups_list=failover_groups,
        azure_update_tag=update_tag,
    )


@timeit
def _load_elastic_pools(neo4j_session, elastic_pools, update_tag):
    """
    Ingest the elastic pool details into neo4j.
    """
    ingest_elastic_pools = """
    UNWIND {elastic_pools_list} as ep
    MERGE (e:AzureElasticPool{id: ep.id})
    ON CREATE SET e.firstseen = timestamp(), e.lastupdated = {azure_update_tag}
    SET e.name = ep.name,
    e.location = ep.location,
    e.kind = ep.kind,
    e.creationdate = ep.creation_date,
    e.state = ep.state,
    e.maxsizebytes = ep.max_size_bytes,
    e.licensetype = ep.license_type,
    e.zoneredundant = ep.zone_redundant
    WITH e, ep
    MATCH (s:AzureServer{id: ep.server_id})
    MERGE (s)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_elastic_pools,
        elastic_pools_list=elastic_pools,
        azure_update_tag=update_tag,
    )


@timeit
def _load_databases(neo4j_session, databases, update_tag):
    """
    Ingest the database details into neo4j.
    """
    ingest_databases = """
    UNWIND {databases_list} as az_database
    MERGE (d:AzureDatabase{id: az_database.id})
    ON CREATE SET d.firstseen = timestamp(), d.lastupdated = {azure_update_tag}
    SET d.name = az_database.name,
    d.location = az_database.location,
    d.kind = az_database.kind,
    d.creationdate = az_database.creation_date,
    d.databaseid = az_database.database_id,
    d.maxsizebytes = az_database.max_size_bytes,
    d.licensetype = az_database.licenseType,
    d.secondarylocation = az_database.default_secondary_location,
    d.elasticpoolid = az_database.elasticPoolId,
    d.collation = az_database.collation,
    d.failovergroupid = az_database.failoverGroupId,
    d.restorabledroppeddbid = az_database.restorableDroppedDatabaseId,
    d.recoverabledbid = az_database.recoverableDatabaseId
    WITH d, az_database
    MATCH (s:AzureServer{id: az_database.server_id})
    MERGE (s)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_databases,
        databases_list=databases,
        azure_update_tag=update_tag,
    )


@timeit
def sync_database_details(neo4j_session, credentials, subscription_id, databases, update_tag):
    db_details = get_database_details(credentials, subscription_id, databases)
    load_database_details(neo4j_session, db_details, update_tag)


@timeit
def get_database_details(credentials, subscription_id, databases):
    """
    Iterate over the databases to get the details of resources in it.
    """
    for database in databases:
        replication_links_list = get_replication_links(credentials, subscription_id, database)
        db_threat_detection_policies = get_db_threat_detection_policies(credentials, subscription_id, database)
        restore_points_list = get_restore_points(credentials, subscription_id, database)
        transparent_data_encryptions = get_transparent_data_encryptions(credentials, subscription_id, database)
        yield database['id'], replication_links_list, db_threat_detection_policies, restore_points_list, transparent_data_encryptions


@timeit
def get_replication_links(credentials, subscription_id, database):
    """
    Returns the details of replication links in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        replication_links = list(map(lambda x: x.as_dict(), client.replication_links.list_by_database(database['resource_group_name'], database['server_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving replication links - {}".format(e))
        return []

    return replication_links


@timeit
def get_db_threat_detection_policies(credentials, subscription_id, database):
    """
    Returns the threat detection policy of a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        db_threat_detection_policies = client.database_threat_detection_policies.get(database['resource_group_name'], database['server_name'], database['name']).as_dict()
    except Exception as e:
        logger.warning("Error while retrieving database threat detection policies - {}".format(e))
        return []

    return db_threat_detection_policies


@timeit
def get_restore_points(credentials, subscription_id, database):
    """
    Returns the details of restore points in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        restore_points_list = list(map(lambda x: x.as_dict(), client.restore_points.list_by_database(database['resource_group_name'], database['server_name'], database['name'])))

    except Exception as e:
        logger.warning("Error while retrieving restore points - {}".format(e))
        return []

    return restore_points_list


@timeit
def get_transparent_data_encryptions(credentials, subscription_id, database):
    """
    Returns the details of transparent data encryptions in a database.
    """
    try:
        client = get_client(credentials, subscription_id)
        transparent_data_encryptions_list = client.transparent_data_encryptions.get(database['resource_group_name'], database['server_name'], database['name']).as_dict()
    except Exception as e:
        logger.warning("Error while retrieving transparent data encryptions - {}".format(e))
        return []

    return transparent_data_encryptions_list


@timeit
def load_database_details(neo4j_session, details, update_tag):
    """
    Create dictionaries for every resource in a database so we can import them in a single query
    """
    replication_links = []
    threat_detection_policies = []
    restore_points = []
    encryptions_list = []

    for databaseId, replication_link, db_threat_detection_policy, restore_point, transparent_data_encryption in details:
        if len(replication_link) > 0:
            for link in replication_link:
                link['database_id'] = databaseId
                replication_links.append(link)

        if len(db_threat_detection_policy) > 0:
            db_threat_detection_policy['database_id'] = databaseId
            threat_detection_policies.append(db_threat_detection_policy)

        if len(restore_point) > 0:
            for point in restore_point:
                point['database_id'] = databaseId
                restore_points.append(point)

        if len(transparent_data_encryption) > 0:
            transparent_data_encryption['database_id'] = databaseId
            encryptions_list.append(transparent_data_encryption)

    _load_replication_links(neo4j_session, replication_links, update_tag)
    _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag)
    _load_restore_points(neo4j_session, restore_points, update_tag)
    _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag)


@timeit
def _load_replication_links(neo4j_session, replication_links, update_tag):
    """
    Ingest replication links into neo4j.
    """
    ingest_replication_links = """
    UNWIND {replication_links_list} as replication_link
    MERGE (rl:AzureReplicationLink{id: replication_link.id})
    ON CREATE SET rl.firstseen = timestamp(), rl.lastupdated = {azure_update_tag}
    SET rl.name = replication_link.name,
    rl.location = replication_link.location,
    rl.partnerdatabase = replication_link.partner_database,
    rl.partnerlocation = replication_link.partner_location,
    rl.partnerrole = replication_link.partner_role,
    rl.partnerserver = replication_link.partner_server,
    rl.mode = replication_link.replication_mode,
    rl.state = replication_link.replication_state,
    rl.percentcomplete = replication_link.percent_complete,
    rl.role = replication_link.role,
    rl.starttime = replication_link.start_time,
    rl.terminationallowed = replication_link.is_termination_allowed
    WITH rl, replication_link
    MATCH (d:AzureDatabase{id: replication_link.database_id})
    MERGE (d)-[r:CONTAINS]->(rl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_replication_links,
        replication_links_list=replication_links,
        azure_update_tag=update_tag,
    )


@timeit
def _load_db_threat_detection_policies(neo4j_session, threat_detection_policies, update_tag):
    """
    Ingest threat detection policy into neo4j.
    """
    ingest_threat_detection_policies = """
    UNWIND {threat_detection_policies_list} as tdp
    MERGE (policy:AzureDatabaseThreatDetectionPolicy{id: tdp.id})
    ON CREATE SET policy.firstseen = timestamp(), policy.lastupdated = {azure_update_tag}
    SET policy.name = tdp.name,
    policy.location = tdp.location,
    policy.kind = tdp.kind,
    policy.emailadmins = tdp.email_account_admins,
    policy.emailaddresses = tdp.email_addresses,
    policy.days = tdp.retention_days,
    policy.state = tdp.state,
    policy.storageendpoint = tdp.storage_endpoint,
    policy.useserverdefault = tdp.use_server_default,
    policy.disabledalerts = tdp.disabled_alerts
    WITH policy, tdp
    MATCH (d:AzureDatabase{id: tdp.database_id})
    MERGE (d)-[r:CONTAINS]->(policy)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_threat_detection_policies,
        threat_detection_policies_list=threat_detection_policies,
        azure_update_tag=update_tag,
    )


@timeit
def _load_restore_points(neo4j_session, restore_points, update_tag):
    """
    Ingest restore points into neo4j.
    """
    ingest_restore_points = """
    UNWIND {restore_points_list} as rp
    MERGE (point:AzureRestorePoint{id: rp.id})
    ON CREATE SET point.firstseen = timestamp(), point.lastupdated = {azure_update_tag}
    SET point.name = rp.name,
    point.location = rp.location,
    point.restoredate = rp.earliest_restore_date,
    point.restorepointtype = rp.restore_point_type,
    point.creationdate = rp.restore_point_creation_date
    WITH point, rp
    MATCH (d:AzureDatabase{id: rp.database_id})
    MERGE (d)-[r:CONTAINS]->(point)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_restore_points,
        restore_points_list=restore_points,
        azure_update_tag=update_tag,
    )


@timeit
def _load_transparent_data_encryptions(neo4j_session, encryptions_list, update_tag):
    """
    Ingest transparent data encryptions into neo4j.
    """
    ingest_data_encryptions = """
    UNWIND {transparent_data_encryptions_list} as e
    MERGE (tae:AzureTransparentDataEncryption{id: e.id})
    ON CREATE SET tae.firstseen = timestamp(), tae.lastupdated = {azure_update_tag}
    SET tae.name = e.name,
    tae.location = e.location,
    tae.status = e.status
    WITH tae, e
    MATCH (d:AzureDatabase{id: e.database_id})
    MERGE (d)-[r:CONTAINS]->(tae)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag}
    """

    neo4j_session.run(
        ingest_data_encryptions,
        transparent_data_encryptions_list=encryptions_list,
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

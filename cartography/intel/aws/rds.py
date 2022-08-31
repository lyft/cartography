import time
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import dict_value_to_str
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_rds_reserved_db_instances_data(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the reserved db instances.
    """
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_reserved_db_instances')
    instances: List[Any] = []
    for page in paginator.paginate():
        instances.extend(page['ReservedDBInstances'])
    for instance in instances:
        instance['region'] = region
        instance['name'] = instance['ReservedDBInstanceArn'].split(':')[-1]
    return instances


def load_rds_reserved_db_instances(session: neo4j.Session, instances: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_rds_reserved_db_instances_tx, instances, current_aws_account_id, aws_update_tag)


@timeit
def _load_rds_reserved_db_instances_tx(
    tx: neo4j.Transaction, data: List[Dict], current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS reserved db instances to neo4j and link them to necessary nodes.
    """
    ingest_rds_reserved_db_instance = """
    UNWIND {Instances} as rds_instance
        MERGE (instance:RDSReservedDBInstance{id: rds_instance.ReservedDBInstanceArn})
        ON CREATE SET instance.firstseen = timestamp(),
            instance.arn = rds_instance.ReservedDBInstanceArn
        SET instance.reserved_db_instance_id = rds_instance.ReservedDBInstanceId,
            instance.name = rds_instance.name,
            instance.reserved_db_instances_offering_id = rds_instance.ReservedDBInstancesOfferingId,
            instance.db_instance_class = rds_instance.DBInstanceClass,
            instance.start_time = rds_instance.StartTime,
            instance.duration = rds_instance.Duration,
            instance.fixed_price = rds_instance.FixedPrice,
            instance.usage_price = rds_instance.UsagePrice,
            instance.currency_code = rds_instance.CurrencyCode,
            instance.db_instance_count = rds_instance.DBInstanceCount,
            instance.product_description = rds_instance.ProductDescription,
            instance.offering_type = rds_instance.OfferingType,
            instance.multi_az = rds_instance.MultiAZ,
            instance.state = rds_instance.State,
            instance.lease_id = rds_instance.LeaseId,
            instance.region = rds_instance.region,
            instance.lastupdated = {aws_update_tag}
        WITH instance
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(instance)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        ingest_rds_reserved_db_instance,
        Instances=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


def cleanup_rds_reserved_db_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_rds_reserved_db_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_rds_reserved_db_instances(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Grab RDS reserved db instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    data = []
    for region in regions:
        logger.info("Syncing RDS reserved db instance for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_rds_reserved_db_instances_data(boto3_session, region))

    logger.info(f"Total RDS Reserved Instances: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('rds', None):
        pageNo = common_job_parameters.get("pagination", {}).get("rds", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("rds", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for rds reserved db instance {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('rds', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['rds']['hasNextPage'] = has_next_page

    load_rds_reserved_db_instances(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_rds_reserved_db_instances(neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_rds_security_groups(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_security_groups')
    secgroups: List[Any] = []
    for page in paginator.paginate():
        secgroups.extend(page['DBSecurityGroups'])
    for secgroup in secgroups:
        secgroup['region'] = region
    return secgroups


def load_rds_security_groups(session: neo4j.Session, secgroups: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_rds_security_groups_tx, secgroups, current_aws_account_id, aws_update_tag)


@timeit
def _load_rds_security_groups_tx(
    tx: neo4j.Transaction, data: List[Dict], current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_rds_secgroup = """
    UNWIND {secgroups} as rds_secgroup
        MERGE (secgroup:RDSSecurityGroup{id: rds_secgroup.DBSecurityGroupArn})
        ON CREATE SET secgroup.firstseen = timestamp(),
            secgroup.arn = rds_secgroup.DBSecurityGroupArn
        SET secgroup.db_security_group_description = rds_secgroup.DBSecurityGroupDescription,
            secgroup.name = rds_secgroup.DBSecurityGroupName,
            secgroup.owner_id = rds_secgroup.OwnerId,
            secgroup.vpc_id = rds_secgroup.VpcId,
            secgroup.lastupdated = {aws_update_tag}
        WITH secgroup
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(secgroup)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        ingest_rds_secgroup,
        secgroups=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


def cleanup_rds_security_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_rds_security_groups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def attach_db_security_groups_to_ec2_security_groups(session: neo4j.Session, data: List[Dict],
                                                     db_sg_id: str, aws_update_tag: int,):
    for sg in data:
        ingest_script = """
        MATCH (dbsg:RDSSecurityGroup{id:{DBSecurityGroupId}})
        MATCH (sg:EC2SecurityGroup{id:{EC2SecurityGroupId}})
        MERGE (dbsg)-[r:USING]->(sg)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """

        session.run(
            ingest_script,
            DBSecurityGroupArn=db_sg_id,
            EC2SecurityGroupId=sg.get('EC2SecurityGroupId'),
            aws_update_tag=aws_update_tag,
        )


@timeit
def sync_rds_security_groups(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        logger.info("Syncing RDS security groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_rds_security_groups(boto3_session, region))

    logger.info(f"Total RDS Security Groups: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('rds', None):
        pageNo = common_job_parameters.get("pagination", {}).get("rds", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("rds", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for rds security group {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('rds', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['rds']['hasNextPage'] = has_next_page

    load_rds_security_groups(neo4j_session, data, current_aws_account_id, update_tag)
    for db_sg in data:
        attach_db_security_groups_to_ec2_security_groups(neo4j_session, db_sg.get(
            'EC2SecurityGroups', []), db_sg.get('DBSecurityGroupArn'), update_tag)
    cleanup_rds_security_groups(neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_rds_snapshots(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_snapshots')
    snapshots: List[Any] = []
    for page in paginator.paginate():
        snapshots.extend(page['DBSnapshots'])
    for snapshot in snapshots:
        snapshot['region'] = region
        snapshot['name'] = snapshot.get('DBSnapshotArn').split(':')[-1]
    return snapshots


def load_rds_snapshots(session: neo4j.Session, snapshots: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_rds_snapshots_tx, snapshots, current_aws_account_id, aws_update_tag)


@timeit
def _load_rds_snapshots_tx(
    tx: neo4j.Transaction, data: List[Dict], current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_rds_snapshot = """
    UNWIND {snapshots} as rds_snapshot
        MERGE (snap:RDSSnapshot{id: rds_snapshot.DBSnapshotArn})
        ON CREATE SET snap.firstseen = timestamp(),
            snap.arn = rds_snapshot.DBSnapshotArn
        SET snap.db_snapshot_identifier = rds_snapshot.DBSnapshotIdentifier,
            snap.name = rds_snapshot.name,
            snap.db_instance_identifier = rds_snapshot.DBInstanceIdentifier,
            snap.snapshot_create_time = rds_snapshot.SnapshotCreateTime,
            snap.engine = rds_snapshot.Engine,
            snap.allocated_storage = rds_snapshot.AllocatedStorage,
            snap.status = rds_snapshot.Status,
            snap.port = rds_snapshot.Port,
            snap.availability_zone = rds_snapshot.AvailabilityZone,
            snap.vpc_id = rds_snapshot.VpcId,
            snap.instance_create_time = rds_snapshot.InstanceCreateTime,
            snap.master_username = rds_snapshot.MasterUsername,
            snap.engine_version = rds_snapshot.EngineVersion,
            snap.license_model = rds_snapshot.LicenseModel,
            snap.snapshot_type = rds_snapshot.SnapshotType,
            snap.option_group_name = rds_snapshot.OptionGroupName,
            snap.percent_progress = rds_snapshot.PercentProgress,
            snap.storage_type = rds_snapshot.StorageType,
            snap.encrypted = rds_snapshot.Encrypted,
            snap.iam_database_authentication_enabled = rds_snapshot.IAMDatabaseAuthenticationEnabled,
            snap.dbi_resource_id = rds_snapshot.DbiResourceId,
            snap.lastupdated = {aws_update_tag}
        WITH snap
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(snap)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        ingest_rds_snapshot,
        snapshots=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


def cleanup_rds_snapshots(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_rds_snapshots_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_rds_snapshots(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        logger.info("Syncing RDS snapshots for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_rds_snapshots(boto3_session, region))

    logger.info(f"Total RDS Snapshots: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('rds', None):
        pageNo = common_job_parameters.get("pagination", {}).get("rds", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("rds", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for rds snapshots {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('rds', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['rds']['hasNextPage'] = has_next_page

    load_rds_snapshots(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_rds_snapshots(neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_rds_cluster_data(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBClusters.
    """
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_clusters')
    clusters: List[Any] = []
    for page in paginator.paginate():
        clusters.extend(page['DBClusters'])
    for cluster in clusters:
        cluster['region'] = region
        cluster['name'] = cluster['DBClusterArn'].split(':')[-1]
    return clusters


@timeit
def load_rds_clusters(
    neo4j_session: neo4j.Session, data: Dict, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS clusters to neo4j and link them to necessary nodes.
    """
    ingest_rds_cluster = """
    UNWIND {Clusters} as rds_cluster
        MERGE (cluster:RDSCluster{id: rds_cluster.DBClusterArn})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = rds_cluster.DBClusterArn
        SET cluster.allocated_storage = rds_cluster.AllocatedStorage,
            cluster.name = rds_cluster.name,
            cluster.availability_zones = rds_cluster.AvailabilityZones,
            cluster.backup_retention_period = rds_cluster.BackupRetentionPeriod,
            cluster.character_set_name = rds_cluster.CharacterSetName,
            cluster.database_name = rds_cluster.DatabaseName,
            cluster.db_cluster_identifier = rds_cluster.DBClusterIdentifier,
            cluster.db_parameter_group = rds_cluster.DBClusterParameterGroup,
            cluster.status = rds_cluster.Status,
            cluster.earliest_restorable_time = rds_cluster.EarliestRestorableTime,
            cluster.endpoint = rds_cluster.Endpoint,
            cluster.reader_endpoint = rds_cluster.ReaderEndpoint,
            cluster.multi_az = rds_cluster.MultiAZ,
            cluster.engine = rds_cluster.Engine,
            cluster.engine_version = rds_cluster.EngineVersion,
            cluster.latest_restorable_time = rds_cluster.LatestRestorableTime,
            cluster.port = rds_cluster.Port,
            cluster.master_username = rds_cluster.MasterUsername,
            cluster.preferred_backup_window = rds_cluster.PreferredBackupWindow,
            cluster.preferred_maintenance_window = rds_cluster.PreferredMaintenanceWindow,
            cluster.hosted_zone_id = rds_cluster.HostedZoneId,
            cluster.storage_encrypted = rds_cluster.StorageEncrypted,
            cluster.kms_key_id = rds_cluster.KmsKeyId,
            cluster.db_cluster_resource_id = rds_cluster.DbClusterResourceId,
            cluster.clone_group_id = rds_cluster.CloneGroupId,
            cluster.cluster_create_time = rds_cluster.ClusterCreateTime,
            cluster.earliest_backtrack_time = rds_cluster.EarliestBacktrackTime,
            cluster.backtrack_window = rds_cluster.BacktrackWindow,
            cluster.backtrack_consumed_change_records = rds_cluster.BacktrackConsumedChangeRecords,
            cluster.capacity = rds_cluster.Capacity,
            cluster.engine_mode = rds_cluster.EngineMode,
            cluster.scaling_configuration_info_min_capacity = rds_cluster.ScalingConfigurationInfoMinCapacity,
            cluster.scaling_configuration_info_max_capacity = rds_cluster.ScalingConfigurationInfoMaxCapacity,
            cluster.scaling_configuration_info_auto_pause = rds_cluster.ScalingConfigurationInfoAutoPause,
            cluster.deletion_protection = rds_cluster.DeletionProtection,
            cluster.region = rds_cluster.region,
            cluster.lastupdated = {aws_update_tag}
        WITH cluster
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    for cluster in data:
        # TODO: track read replicas
        # TODO: track associated roles
        # TODO: track security groups
        # TODO: track subnet groups

        cluster['EarliestRestorableTime'] = dict_value_to_str(cluster, 'EarliestRestorableTime')
        cluster['LatestRestorableTime'] = dict_value_to_str(cluster, 'LatestRestorableTime')
        cluster['ClusterCreateTime'] = dict_value_to_str(cluster, 'ClusterCreateTime')
        cluster['EarliestBacktrackTime'] = dict_value_to_str(cluster, 'EarliestBacktrackTime')
        cluster['ScalingConfigurationInfoMinCapacity'] = cluster.get('ScalingConfigurationInfo', {}).get('MinCapacity')
        cluster['ScalingConfigurationInfoMaxCapacity'] = cluster.get('ScalingConfigurationInfo', {}).get('MaxCapacity')
        cluster['ScalingConfigurationInfoAutoPause'] = cluster.get('ScalingConfigurationInfo', {}).get('AutoPause')

    neo4j_session.run(
        ingest_rds_cluster,
        Clusters=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
@aws_handle_regions
def get_rds_instance_data(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBInstances.
    """
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_instances')
    instances: List[Any] = []
    for page in paginator.paginate():
        instances.extend(page['DBInstances'])
    for instance in instances:
        instance['region'] = region
    return instances


@timeit
def load_rds_instances(
    neo4j_session: neo4j.Session, data: Dict, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS instances to neo4j and link them to necessary nodes.
    """
    ingest_rds_instance = """
    UNWIND {Instances} as rds_instance
        MERGE (rds:RDSInstance{id: rds_instance.DBInstanceArn})
        ON CREATE SET rds.firstseen = timestamp(),
            rds.arn = rds_instance.DBInstanceArn
        SET rds.db_instance_identifier = rds_instance.DBInstanceIdentifier,
            rds.db_instance_class = rds_instance.DBInstanceClass,
            rds.engine = rds_instance.Engine,
            rds.master_username = rds_instance.MasterUsername,
            rds.db_name = rds_instance.DBName,
            rds.instance_create_time = rds_instance.InstanceCreateTime,
            rds.availability_zone = rds_instance.AvailabilityZone,
            rds.multi_az = rds_instance.MultiAZ,
            rds.engine_version = rds_instance.EngineVersion,
            rds.publicly_accessible = rds_instance.PubliclyAccessible,
            rds.db_cluster_identifier = rds_instance.DBClusterIdentifier,
            rds.storage_encrypted = rds_instance.StorageEncrypted,
            rds.kms_key_id = rds_instance.KmsKeyId,
            rds.dbi_resource_id = rds_instance.DbiResourceId,
            rds.ca_certificate_identifier = rds_instance.CACertificateIdentifier,
            rds.enhanced_monitoring_resource_arn = rds_instance.EnhancedMonitoringResourceArn,
            rds.monitoring_role_arn = rds_instance.MonitoringRoleArn,
            rds.performance_insights_enabled = rds_instance.PerformanceInsightsEnabled,
            rds.performance_insights_kms_key_id = rds_instance.PerformanceInsightsKMSKeyId,
            rds.region = rds_instance.region,
            rds.consolelink = rds_instance.consolelink,
            rds.deletion_protection = rds_instance.DeletionProtection,
            rds.preferred_backup_window = rds_instance.PreferredBackupWindow,
            rds.latest_restorable_time = rds_instance.LatestRestorableTime,
            rds.preferred_maintenance_window = rds_instance.PreferredMaintenanceWindow,
            rds.backup_retention_period = rds_instance.BackupRetentionPeriod,
            rds.endpoint_address = rds_instance.EndpointAddress,
            rds.endpoint_hostedzoneid = rds_instance.EndpointHostedZoneId,
            rds.endpoint_port = rds_instance.EndpointPort,
            rds.iam_database_authentication_enabled = rds_instance.IAMDatabaseAuthenticationEnabled,
            rds.auto_minor_version_upgrade = rds_instance.AutoMinorVersionUpgrade,
            rds.lastupdated = {aws_update_tag}
        WITH rds
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(rds)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    read_replicas = []
    clusters = []
    secgroups = []
    subnets = []

    for rds in data:
        ep = _validate_rds_endpoint(rds)

        # Keep track of instances that are read replicas so we can attach them to their source instances later
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        # Keep track of instances that are cluster members so we can attach them to their source clusters later
        if rds.get("DBClusterIdentifier"):
            clusters.append(rds)

        if rds.get('VpcSecurityGroups'):
            secgroups.append(rds)

        if rds.get('DBSubnetGroup'):
            subnets.append(rds)

        rds['InstanceCreateTime'] = dict_value_to_str(rds, 'InstanceCreateTime')
        rds['LatestRestorableTime'] = dict_value_to_str(rds, 'LatestRestorableTime')
        rds['EndpointAddress'] = ep.get('Address')
        rds['EndpointHostedZoneId'] = ep.get('HostedZoneId')
        rds['EndpointPort'] = ep.get('Port')
        rds['consolelink'] = aws_console_link.get_console_link(arn=rds['DBInstanceArn'])
    neo4j_session.run(
        ingest_rds_instance,
        Instances=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )
    _attach_ec2_security_groups(neo4j_session, secgroups, aws_update_tag)
    _attach_ec2_subnet_groups(neo4j_session, subnets, current_aws_account_id, aws_update_tag)
    _attach_read_replicas(neo4j_session, read_replicas, aws_update_tag)
    _attach_clusters(neo4j_session, clusters, aws_update_tag)


@timeit
def _attach_ec2_subnet_groups(
    neo4j_session: neo4j.Session, instances: List[Dict], current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Attach RDS instances to their EC2 subnet groups
    """
    attach_rds_to_subnet_group = """
    UNWIND {SubnetGroups} as rds_sng
        MERGE (sng:DBSubnetGroup{id: rds_sng.arn})
        ON CREATE SET sng.firstseen = timestamp()
        SET sng.name = rds_sng.DBSubnetGroupName,
            sng.vpc_id = rds_sng.VpcId,
            sng.description = rds_sng.DBSubnetGroupDescription,
            sng.status = rds_sng.DBSubnetGroupStatus,
            sng.lastupdated = {aws_update_tag},
            sng.arn = rds_sng.arn
        WITH sng, rds_sng.instance_arn AS instance_arn
        MATCH(rds:RDSInstance{id: instance_arn})
        MERGE(rds)-[r:MEMBER_OF_DB_SUBNET_GROUP]->(sng)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    db_sngs = []
    for instance in instances:
        region = instance['region']
        db_sng = instance['DBSubnetGroup']
        db_sng['arn'] = _get_db_subnet_group_arn(region, current_aws_account_id, db_sng['DBSubnetGroupName'])
        db_sng['instance_arn'] = instance['DBInstanceArn']
        db_sng['region'] = region
        db_sngs.append(db_sng)
    neo4j_session.run(
        attach_rds_to_subnet_group,
        SubnetGroups=db_sngs,
        aws_update_tag=aws_update_tag,
    )
    _attach_ec2_subnets_to_subnetgroup(neo4j_session, db_sngs, current_aws_account_id, aws_update_tag)


@timeit
def _attach_ec2_subnets_to_subnetgroup(
    neo4j_session: neo4j.Session, db_subnet_groups: List[Dict],
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    """
    Attach EC2Subnets to their DB Subnet Group.

    From https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html:
    `Each DB subnet group should have subnets in at least two Availability Zones in a given region. When creating a DB
    instance in a VPC, you must select a DB subnet group. Amazon RDS uses that DB subnet group and your preferred
    Availability Zone to select a subnet and an IP address within that subnet to associate with your DB instance.`
    """
    attach_subnets_to_sng = """
    UNWIND {Subnets} as rds_sn
        MATCH(sng:DBSubnetGroup{id: rds_sn.sng_arn})
        MERGE(subnet:EC2Subnet{subnetid: rds_sn.sn_id})
        ON CREATE SET subnet.firstseen = timestamp()
        MERGE(sng)-[r:RESOURCE]->(subnet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag},
        subnet.availability_zone = rds_sn.az,
        subnet.lastupdated = {aws_update_tag}
    """
    subnets = []
    for subnet_group in db_subnet_groups:
        region = subnet_group['region']
        for subnet in subnet_group.get('Subnets', []):
            sn_id = subnet.get('SubnetIdentifier')
            sng_arn = _get_db_subnet_group_arn(region, current_aws_account_id, subnet_group['DBSubnetGroupName'])
            az = subnet.get('SubnetAvailabilityZone', {}).get('Name')
            subnets.append({
                'sn_id': sn_id,
                'sng_arn': sng_arn,
                'az': az,
            })
    neo4j_session.run(
        attach_subnets_to_sng,
        Subnets=subnets,
        aws_update_tag=aws_update_tag,
    )


@timeit
def _attach_ec2_security_groups(neo4j_session: neo4j.Session, instances: List[Dict], aws_update_tag: int) -> None:
    """
    Attach an RDS instance to its EC2SecurityGroups
    """
    attach_rds_to_group = """
    UNWIND {Groups} as rds_sg
        MATCH (rds:RDSInstance{id: rds_sg.arn})
        MERGE (sg:EC2SecurityGroup{id: rds_sg.group_id})
        MERGE (rds)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        ON CREATE SET m.firstseen = timestamp()
        SET m.lastupdated = {aws_update_tag}
    """
    groups = []
    for instance in instances:
        for group in instance['VpcSecurityGroups']:
            groups.append({
                'arn': instance['DBInstanceArn'],
                'group_id': group['VpcSecurityGroupId'],
            })
    neo4j_session.run(
        attach_rds_to_group,
        Groups=groups,
        aws_update_tag=aws_update_tag,
    )


@timeit
def _attach_read_replicas(neo4j_session: neo4j.Session, read_replicas: List[Dict], aws_update_tag: int) -> None:
    """
    Attach read replicas to their source instances
    """
    attach_replica_to_source = """
    UNWIND {Replicas} as rds_replica
        MATCH (replica:RDSInstance{id: rds_replica.DBInstanceArn}),
        (source:RDSInstance{db_instance_identifier: rds_replica.ReadReplicaSourceDBInstanceIdentifier})
        MERGE (replica)-[r:IS_READ_REPLICA_OF]->(source)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        attach_replica_to_source,
        Replicas=read_replicas,
        aws_update_tag=aws_update_tag,
    )


@timeit
def _attach_clusters(neo4j_session: neo4j.Session, cluster_members: List[Dict], aws_update_tag: int) -> None:
    """
    Attach cluster members to their source clusters
    """
    attach_member_to_source = """
    UNWIND {Members} as rds_cluster_member
    MATCH (member:RDSInstance{id: rds_cluster_member.DBInstanceArn}),
    (source:RDSCluster{db_cluster_identifier: rds_cluster_member.DBClusterIdentifier})
    MERGE (member)-[r:IS_CLUSTER_MEMBER_OF]->(source)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        attach_member_to_source,
        Members=cluster_members,
        aws_update_tag=aws_update_tag,
    )


def _validate_rds_endpoint(rds: Dict) -> Dict:
    """
    Get Endpoint from RDS data structure.  Log to debug if an Endpoint field does not exist.
    """
    ep = rds.get('Endpoint', {})
    if not ep:
        logger.debug("RDS instance does not have an Endpoint field.  Here is the object: %r", rds)
    return ep


def _get_db_subnet_group_arn(region: str, current_aws_account_id: str, db_subnet_group_name: str) -> str:
    """
    Return an ARN for the DB subnet group name by concatenating the account name and region.
    This is done to avoid another AWS API call since the describe_db_instances boto call does not return the DB subnet
    group ARN.
    Form is arn:aws:rds:{region}:{account-id}:subgrp:{subnet-group-name}
    as per https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    """
    return f"arn:aws:rds:{region}:{current_aws_account_id}:subgrp:{db_subnet_group_name}"


@timeit
def cleanup_rds_instances_and_db_subnet_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove RDS graph nodes and DBSubnetGroups that were created from other ingestion runs
    """
    run_cleanup_job('aws_import_rds_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_rds_clusters(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Remove RDS cluster graph nodes
    """
    run_cleanup_job('aws_import_rds_clusters_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_rds_clusters(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    data = []
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_rds_cluster_data(boto3_session, region))

    logger.info(f"Total RDS Clusters: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('rds', None):
        pageNo = common_job_parameters.get("pagination", {}).get("rds", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("rds", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for rds cluster {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('rds', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['rds']['hasNextPage'] = has_next_page

    load_rds_clusters(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_rds_clusters(neo4j_session, common_job_parameters)


@timeit
def sync_rds_instances(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    data = []
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_rds_instance_data(boto3_session, region))

    logger.info(f"Total RDS Instances: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('rds', None):
        pageNo = common_job_parameters.get("pagination", {}).get("rds", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("rds", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for rds instance {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('rds', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('rds', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['rds']['hasNextPage'] = has_next_page

    load_rds_instances(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_rds_instances_and_db_subnet_groups(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing RDS for account '%s', at %s.", current_aws_account_id, tic)

    sync_rds_clusters(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    sync_rds_instances(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    sync_rds_reserved_db_instances(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    sync_rds_security_groups(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    sync_rds_snapshots(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    toc = time.perf_counter()
    logger.info(f"Time to process RDS: {toc - tic:0.4f} seconds")

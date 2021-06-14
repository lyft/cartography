import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _dict_value_to_str(obj: Dict, key: str) -> Optional[str]:
    """
    Convert the value referenced by the key in the dict to a string, if it exists, and return it. If it doesn't exist,
    return None.
    """
    value = obj.get(key)
    if value is not None:
        return str(value)
    else:
        return None


@timeit
@aws_handle_regions
def get_rds_cluster_data(boto3_session: boto3.session.Session, region: str) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBClusters.
    """
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_clusters')
    instances: List[Any] = []
    for page in paginator.paginate():
        instances.extend(page['DBClusters'])

    return instances


@timeit
def load_rds_clusters(
    neo4j_session: neo4j.Session, data: Dict, region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS clusters to neo4j and link them to necessary nodes.
    """
    ingest_rds_cluster = """
    MERGE (cluster:RDSCluster{id: {DBClusterArn}})
    ON CREATE SET cluster.firstseen = timestamp()
    SET cluster.arn = {DBClusterArn},
    cluster.allocated_storage = {AllocatedStorage},
    cluster.availability_zones = {AvailabilityZones},
    cluster.backup_retention_period = {BackupRetentionPeriod},
    cluster.character_set_name = {CharacterSetName},
    cluster.database_name = {DatabaseName},
    cluster.db_cluster_identifier = {DBClusterIdentifier},
    cluster.db_parameter_group = {DBClusterParameterGroup},
    cluster.status = {Status},
    cluster.earliest_restorable_time = {EarliestRestorableTime},
    cluster.endpoint = {Endpoint},
    cluster.reader_endpoint = {ReaderEndpoint},
    cluster.multi_az = {MultiAZ},
    cluster.engine = {Engine},
    cluster.engine_version = {EngineVersion},
    cluster.latest_restorable_time = {LatestRestorableTime},
    cluster.port = {Port},
    cluster.master_username = {MasterUsername},
    cluster.preferred_backup_window = {PreferredBackupWindow},
    cluster.preferred_maintenance_window = {PreferredMaintenanceWindow},
    cluster.hosted_zone_id = {HostedZoneId},
    cluster.storage_encrypted = {StorageEncrypted},
    cluster.kms_key_id = {KmsKeyId},
    cluster.db_cluster_resource_id = {DbClusterResourceId},
    cluster.clone_group_id = {CloneGroupId},
    cluster.cluster_create_time = {ClusterCreateTime},
    cluster.earliest_backtrack_time = {EarliestBacktrackTime},
    cluster.backtrack_window = {BacktrackWindow},
    cluster.backtrack_consumed_change_records = {BacktrackConsumedChangeRecords},
    cluster.capacity = {Capacity},
    cluster.engine_mode = {EngineMode},
    cluster.scaling_configuration_info_min_capacity = {ScalingConfigurationInfoMinCapacity},
    cluster.scaling_configuration_info_max_capacity = {ScalingConfigurationInfoMaxCapacity},
    cluster.scaling_configuration_info_auto_pause = {ScalingConfigurationInfoAutoPause},
    cluster.deletion_protection = {DeletionProtection},
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

        neo4j_session.run(
            ingest_rds_cluster,
            DBClusterArn=cluster['DBClusterArn'],
            AllocatedStorage=cluster.get('AllocatedStorage'),
            AvailabilityZones=cluster.get('AvailabilityZones', []),
            BackupRetentionPeriod=cluster.get('BackupRetentionPeriod'),
            CharacterSetName=cluster.get('CharacterSetName'),
            DatabaseName=cluster.get('DatabaseName'),
            DBClusterIdentifier=cluster.get('DBClusterIdentifier'),
            DBClusterParameterGroup=cluster.get('DBClusterParameterGroup'),
            Status=cluster.get('Status'),
            EarliestRestorableTime=_dict_value_to_str(cluster, 'EarliestRestorableTime'),
            Endpoint=cluster.get('Endpoint'),
            ReaderEndpoint=cluster.get('ReaderEndpoint'),
            MultiAZ=cluster.get('MultiAZ'),
            Engine=cluster.get('Engine'),
            EngineVersion=cluster.get('EngineVersion'),
            LatestRestorableTime=_dict_value_to_str(cluster, 'LatestRestorableTime'),
            Port=cluster.get('Port'),
            MasterUsername=cluster.get('MasterUsername'),
            PreferredBackupWindow=cluster.get('PreferredBackupWindow'),
            PreferredMaintenanceWindow=cluster.get('PreferredMaintenanceWindow'),
            HostedZoneId=cluster.get('HostedZoneId'),
            StorageEncrypted=cluster.get('StorageEncrypted'),
            KmsKeyId=cluster.get('KmsKeyId'),
            DbClusterResourceId=cluster.get('DbClusterResourceId'),
            CloneGroupId=cluster.get('CloneGroupId'),
            ClusterCreateTime=_dict_value_to_str(cluster, 'ClusterCreateTime'),
            EarliestBacktrackTime=_dict_value_to_str(cluster, 'EarliestBacktrackTime'),
            BacktrackWindow=cluster.get('BacktrackWindow'),
            BacktrackConsumedChangeRecords=cluster.get('BacktrackConsumedChangeRecords'),
            Capacity=cluster.get('Capacity'),
            EngineMode=cluster.get('EngineMode'),
            ScalingConfigurationInfoMinCapacity=cluster.get('ScalingConfigurationInfo', {}).get('MinCapacity'),
            ScalingConfigurationInfoMaxCapacity=cluster.get('ScalingConfigurationInfo', {}).get('MaxCapacity'),
            ScalingConfigurationInfoAutoPause=cluster.get('ScalingConfigurationInfo', {}).get('AutoPause'),
            DeletionProtection=cluster.get('DeletionProtection'),
            Region=region,
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

    return instances


@timeit
def load_rds_instances(
    neo4j_session: neo4j.Session, data: Dict, region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS instances to neo4j and link them to necessary nodes.
    """
    ingest_rds_instance = """
    MERGE (rds:RDSInstance{id: {DBInstanceArn}})
    ON CREATE SET rds.firstseen = timestamp()
    SET rds.arn = {DBInstanceArn},
    rds.db_instance_identifier = {DBInstanceIdentifier},
    rds.db_instance_class = {DBInstanceClass},
    rds.engine = {Engine},
    rds.master_username = {MasterUsername},
    rds.db_name = {DBName},
    rds.instance_create_time = {InstanceCreateTime},
    rds.availability_zone = {AvailabilityZone},
    rds.multi_az = {MultiAZ},
    rds.engine_version = {EngineVersion},
    rds.publicly_accessible = {PubliclyAccessible},
    rds.db_cluster_identifier = {DBClusterIdentifier},
    rds.storage_encrypted = {StorageEncrypted},
    rds.kms_key_id = {KmsKeyId},
    rds.dbi_resource_id = {DbiResourceId},
    rds.ca_certificate_identifier = {CACertificateIdentifier},
    rds.enhanced_monitoring_resource_arn = {EnhancedMonitoringResourceArn},
    rds.monitoring_role_arn = {MonitoringRoleArn},
    rds.performance_insights_enabled = {PerformanceInsightsEnabled},
    rds.performance_insights_kms_key_id = {PerformanceInsightsKMSKeyId},
    rds.region = {Region},
    rds.deletion_protection = {DeletionProtection},
    rds.preferred_backup_window = {PreferredBackupWindow},
    rds.latest_restorable_time = {LatestRestorableTime},
    rds.preferred_maintenance_window = {PreferredMaintenanceWindow},
    rds.backup_retention_period = {BackupRetentionPeriod},
    rds.endpoint_address = {EndpointAddress},
    rds.endpoint_hostedzoneid = {EndpointHostedZoneId},
    rds.endpoint_port = {EndpointPort},
    rds.iam_database_authentication_enabled = {IAMDatabaseAuthenticationEnabled},
    rds.auto_minor_version_upgrade = {AutoMinorVersionUpgrade},
    rds.lastupdated = {aws_update_tag}
    WITH rds
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(rds)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    read_replicas = []
    clusters = []

    for rds in data:
        ep = _validate_rds_endpoint(rds)

        # Keep track of instances that are read replicas so we can attach them to their source instances later
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        # Keep track of instances that are cluster members so we can attach them to their source clusters later
        if rds.get("DBClusterIdentifier"):
            clusters.append(rds)

        neo4j_session.run(
            ingest_rds_instance,
            DBInstanceArn=rds['DBInstanceArn'],
            DBInstanceIdentifier=rds['DBInstanceIdentifier'],
            DBInstanceClass=rds.get('DBInstanceClass'),
            Engine=rds.get('Engine'),
            MasterUsername=rds.get('MasterUsername'),
            DBName=rds.get('DBName'),
            InstanceCreateTime=_dict_value_to_str(rds, 'InstanceCreateTime'),
            AvailabilityZone=rds.get('AvailabilityZone'),
            MultiAZ=rds.get('MultiAZ'),
            EngineVersion=rds.get('EngineVersion'),
            PubliclyAccessible=rds.get('PubliclyAccessible'),
            DBClusterIdentifier=rds.get('DBClusterIdentifier'),
            StorageEncrypted=rds.get('StorageEncrypted'),
            KmsKeyId=rds.get('KmsKeyId'),
            DbiResourceId=rds.get('DbiResourceId'),
            CACertificateIdentifier=rds.get('CACertificateIdentifier'),
            EnhancedMonitoringResourceArn=rds.get('EnhancedMonitoringResourceArn'),
            MonitoringRoleArn=rds.get('MonitoringRoleArn'),
            PerformanceInsightsEnabled=rds.get('PerformanceInsightsEnabled'),
            PerformanceInsightsKMSKeyId=rds.get('PerformanceInsightsKMSKeyId'),
            DeletionProtection=rds.get('DeletionProtection'),
            BackupRetentionPeriod=rds.get('BackupRetentionPeriod'),
            PreferredBackupWindow=rds.get('PreferredBackupWindow'),
            LatestRestorableTime=_dict_value_to_str(rds, 'LatestRestorableTime'),
            PreferredMaintenanceWindow=rds.get('PreferredMaintenanceWindow'),
            EndpointAddress=ep.get('Address'),
            EndpointHostedZoneId=ep.get('HostedZoneId'),
            EndpointPort=ep.get('Port'),
            IAMDatabaseAuthenticationEnabled=rds.get('IAMDatabaseAuthenticationEnabled'),
            AutoMinorVersionUpgrade=rds.get('AutoMinorVersionUpgrade'),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        _attach_ec2_security_groups(neo4j_session, rds, aws_update_tag)
        _attach_ec2_subnet_groups(neo4j_session, rds, region, current_aws_account_id, aws_update_tag)
    _attach_read_replicas(neo4j_session, read_replicas, aws_update_tag)
    _attach_clusters(neo4j_session, clusters, aws_update_tag)


@timeit
def _attach_ec2_subnet_groups(
    neo4j_session: neo4j.Session, instance: dict, region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Attach RDS instance to its EC2 subnets
    """
    attach_rds_to_subnet_group = """
    MERGE(sng:DBSubnetGroup{id:{sng_arn}})
    ON CREATE SET sng.firstseen = timestamp()
    SET sng.name = {DBSubnetGroupName},
    sng.vpc_id = {VpcId},
    sng.description = {DBSubnetGroupDescription},
    sng.status = {DBSubnetGroupStatus},
    sng.lastupdated = {aws_update_tag}
    WITH sng
    MATCH(rds:RDSInstance{id:{DBInstanceArn}})
    MERGE(rds)-[r:MEMBER_OF_DB_SUBNET_GROUP]->(sng)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    if 'DBSubnetGroup' in instance:
        db_sng = instance['DBSubnetGroup']
        arn = _get_db_subnet_group_arn(region, current_aws_account_id, db_sng['DBSubnetGroupName'])
        neo4j_session.run(
            attach_rds_to_subnet_group,
            sng_arn=arn,
            DBSubnetGroupName=db_sng['DBSubnetGroupName'],
            VpcId=db_sng.get("VpcId"),
            DBSubnetGroupDescription=db_sng.get('DBSubnetGroupDescription'),
            DBSubnetGroupStatus=db_sng.get('SubnetGroupStatus'),
            DBInstanceArn=instance['DBInstanceArn'],
            aws_update_tag=aws_update_tag,
        )
        _attach_ec2_subnets_to_subnetgroup(neo4j_session, db_sng, region, current_aws_account_id, aws_update_tag)


@timeit
def _attach_ec2_subnets_to_subnetgroup(
    neo4j_session: neo4j.Session, db_subnet_group: Dict, region: str,
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    """
    Attach EC2Subnets to the DB Subnet Group.

    From https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html:
    `Each DB subnet group should have subnets in at least two Availability Zones in a given region. When creating a DB
    instance in a VPC, you must select a DB subnet group. Amazon RDS uses that DB subnet group and your preferred
    Availability Zone to select a subnet and an IP address within that subnet to associate with your DB instance.`
    """
    attach_subnets_to_sng = """
    MATCH(sng:DBSubnetGroup{id:{sng_arn}})
    MERGE(subnet:EC2Subnet{subnetid:{SubnetIdentifier}})
    ON CREATE SET subnet.firstseen = timestamp()
    MERGE(sng)-[r:RESOURCE]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag},
    subnet.availability_zone = {SubnetAvailabilityZone},
    subnet.lastupdated = {aws_update_tag}
    """
    for sn in db_subnet_group.get('Subnets', []):
        subnet_id = sn.get('SubnetIdentifier')
        arn = _get_db_subnet_group_arn(region, current_aws_account_id, db_subnet_group['DBSubnetGroupName'])
        neo4j_session.run(
            attach_subnets_to_sng,
            SubnetIdentifier=subnet_id,
            sng_arn=arn,
            aws_update_tag=aws_update_tag,
            SubnetAvailabilityZone=sn.get('SubnetAvailabilityZone', {}).get('Name'),
        )


@timeit
def _attach_ec2_security_groups(neo4j_session: neo4j.Session, instance: Dict, aws_update_tag: int) -> None:
    """
    Attach an RDS instance to its EC2SecurityGroups
    """
    attach_rds_to_group = """
    MATCH (rds:RDSInstance{id:{RdsArn}})
    MERGE (sg:EC2SecurityGroup{id:{GroupId}})
    MERGE (rds)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {aws_update_tag}
    """
    for group in instance.get('VpcSecurityGroups', []):
        neo4j_session.run(
            attach_rds_to_group,
            RdsArn=instance['DBInstanceArn'],
            GroupId=group['VpcSecurityGroupId'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_read_replicas(neo4j_session: neo4j.Session, read_replicas: Dict, aws_update_tag: int) -> None:
    """
    Attach read replicas to their source instances
    """
    attach_replica_to_source = """
    MATCH (replica:RDSInstance{id:{ReplicaArn}}),
    (source:RDSInstance{db_instance_identifier:{SourceInstanceIdentifier}})
    MERGE (replica)-[r:IS_READ_REPLICA_OF]->(source)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for replica in read_replicas:
        neo4j_session.run(
            attach_replica_to_source,
            ReplicaArn=replica['DBInstanceArn'],
            SourceInstanceIdentifier=replica['ReadReplicaSourceDBInstanceIdentifier'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_clusters(neo4j_session: neo4j.Session, cluster_members: Dict, aws_update_tag: int) -> None:
    """
    Attach cluster members to their source clusters
    """
    attach_member_to_source = """
    MATCH (member:RDSInstance{id:{DBInstanceArn}}),
    (source:RDSCluster{db_cluster_identifier:{DBClusterIdentifier}})
    MERGE (member)-[r:IS_CLUSTER_MEMBER_OF]->(source)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for member in cluster_members:
        neo4j_session.run(
            attach_member_to_source,
            DBInstanceArn=member['DBInstanceArn'],
            DBClusterIdentifier=member['DBClusterIdentifier'],
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
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_rds_cluster_data(boto3_session, region)
        load_rds_clusters(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_rds_clusters(neo4j_session, common_job_parameters)


@timeit
def sync_rds_instances(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_rds_instance_data(boto3_session, region)
        load_rds_instances(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_rds_instances_and_db_subnet_groups(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    sync_rds_clusters(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )
    sync_rds_instances(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag,
        common_job_parameters,
    )

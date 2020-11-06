import logging

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_rds_instance_data(boto3_session, region):
    """
    Create an RDS boto3 client and grab all the DBInstances.
    """
    client = boto3_session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_instances')
    instances = []
    for page in paginator.paginate():
        instances.extend(page['DBInstances'])

    return instances


@timeit
def load_rds_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
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

    for rds in data:
        instance_create_time = str(rds['InstanceCreateTime']) if 'InstanceCreateTime' in rds else None
        latest_restorable_time = str(rds['LatestRestorableTime']) if 'LatestRestorableTime' in rds else None

        ep = _validate_rds_endpoint(rds)

        # Keep track of instances that are read replicas so we can attach them to their source instances later
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        neo4j_session.run(
            ingest_rds_instance,
            DBInstanceArn=rds['DBInstanceArn'],
            DBInstanceIdentifier=rds['DBInstanceIdentifier'],
            DBInstanceClass=rds.get('DBInstanceClass'),
            Engine=rds.get('Engine'),
            MasterUsername=rds.get('MasterUsername'),
            DBName=rds.get('DBName'),
            InstanceCreateTime=instance_create_time,
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
            LatestRestorableTime=latest_restorable_time,
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


@timeit
def _attach_ec2_subnet_groups(neo4j_session, instance, region, current_aws_account_id, aws_update_tag):
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
def _attach_ec2_subnets_to_subnetgroup(neo4j_session, db_subnet_group, region, current_aws_account_id, aws_update_tag):
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
def _attach_ec2_security_groups(neo4j_session, instance, aws_update_tag):
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
def _attach_read_replicas(neo4j_session, read_replicas, aws_update_tag):
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


def _validate_rds_endpoint(rds):
    """
    Get Endpoint from RDS data structure.  Log to debug if an Endpoint field does not exist.
    """
    ep = rds.get('Endpoint', {})
    if not ep:
        logger.debug("RDS instance does not have an Endpoint field.  Here is the object: %r", rds)
    return ep


def _get_db_subnet_group_arn(region, current_aws_account_id, db_subnet_group_name):
    """
    Return an ARN for the DB subnet group name by concatenating the account name and region.
    This is done to avoid another AWS API call since the describe_db_instances boto call does not return the DB subnet
    group ARN.
    Form is arn:aws:rds:{region}:{account-id}:subgrp:{subnet-group-name}
    as per https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    """
    return f"arn:aws:rds:{region}:{current_aws_account_id}:subgrp:{db_subnet_group_name}"


@timeit
def cleanup_rds_instances_and_db_subnet_groups(neo4j_session, common_job_parameters):
    """
    Remove RDS graph nodes and DBSubnetGroups that were created from other ingestion runs
    """
    run_cleanup_job('aws_import_rds_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_rds_instances(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_rds_instance_data(boto3_session, region)
        load_rds_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_rds_instances_and_db_subnet_groups(neo4j_session, common_job_parameters)


def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    sync_rds_instances(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

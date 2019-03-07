import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_rds_instance_data(session, region):
    """
    Create an RDS boto3 client and grab all the DBInstances.
    """
    client = session.client('rds', region_name=region)
    paginator = client.get_paginator('describe_db_instances')
    instances = []
    for page in paginator.paginate():
        instances.extend(page['DBInstances'])
    return {'DBInstances': instances}


def load_rds_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    """
    Ingest the RDS instances to neo4j and link them to necessary nodes.
    """
    ingest_rds_instance = """
    MERGE (rds:RDSInstance{id: {DBInstanceArn}})
    ON CREATE SET rds.firstseen = timestamp()
    SET rds.db_instance_identifier = {DBInstanceIdentifier},
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
    rds.lastupdated = {aws_update_tag}
    WITH rds
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(rds)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    read_replicas = []

    for rds in data.get('DBInstances', []):
        instance_create_time = str(rds['InstanceCreateTime']) if 'InstanceCreateTime' in rds else None
        latest_restorable_time = str(rds['LatestRestorableTime']) if 'LatestRestorableTime' in rds else None

        ep = _validate_rds_endpoint(rds)

        # Keep track of instances that are read replicas so we can attach them to their source instances later
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        neo4j_session.run(
            ingest_rds_instance,
            DBInstanceArn=rds['DBInstanceArn'],
            DBInstanceIdentifier=rds.get('DBInstanceIdentifier', None),
            DBInstanceClass=rds.get('DBInstanceClass', None),
            Engine=rds.get('Engine', None),
            MasterUsername=rds.get('MasterUsername', None),
            DBName=rds.get('DBName', None),
            InstanceCreateTime=instance_create_time,
            AvailabilityZone=rds.get('AvailabilityZone', None),
            MultiAZ=rds.get('MultiAZ', None),
            EngineVersion=rds.get('EngineVersion', None),
            PubliclyAccessible=rds.get('PubliclyAccessible', None),
            DBClusterIdentifier=rds.get('DBClusterIdentifier', None),
            StorageEncrypted=rds.get('StorageEncrypted', None),
            KmsKeyId=rds.get('KmsKeyId', None),
            DbiResourceId=rds.get('DbiResourceId', None),
            CACertificateIdentifier=rds.get('CACertificateIdentifier', None),
            EnhancedMonitoringResourceArn=rds.get('EnhancedMonitoringResourceArn', None),
            MonitoringRoleArn=rds.get('MonitoringRoleArn', None),
            PerformanceInsightsEnabled=rds.get('PerformanceInsightsEnabled', None),
            PerformanceInsightsKMSKeyId=rds.get('PerformanceInsightsKMSKeyId', None),
            DeletionProtection=rds.get('DeletionProtection', None),
            BackupRetentionPeriod=rds.get('BackupRetentionPeriod', None),
            PreferredBackupWindow=rds.get('PreferredBackupWindow', None),
            LatestRestorableTime=latest_restorable_time,
            PreferredMaintenanceWindow=rds.get('PreferredMaintenanceWindow', None),
            EndpointAddress=ep.get('Address', None),
            EndpointHostedZoneId=ep.get('HostedZoneId', None),
            EndpointPort=ep.get('Port', None),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag
        )
        _attach_ec2_security_groups(neo4j_session, rds, aws_update_tag)
        _attach_ec2_subnet_groups(neo4j_session, rds, aws_update_tag)
    _attach_read_replicas(neo4j_session, read_replicas, aws_update_tag)


def _attach_ec2_subnet_groups(neo4j_session, instance, aws_update_tag):
    """
    Attach RDS instance to its EC2 subnets
    """
    attach_rds_to_subnet_group = """
    MERGE(sng:DBSubnetGroup{id:{DBSubnetGroupName}})
    ON CREATE SET sng.firstseen = timestamp()
    SET sng.vpc_id = {VpcId},
    sng.description = {DBSubnetGroupDescription},
    sng.status = {DBSubnetGroupStatus}
    WITH sng
    MATCH(rds:RDSInstance{id:{DBInstanceArn}})
    MERGE(rds)-[r:PART_OF_DB_SUBNET_GROUP]->(sng)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    if not instance.get('DBInstanceArn'):
        logger.debug("Expected RDSInstance to have a DBInstanceArn but it doesn't.  Here is the object: %s", instance)
    elif not instance.get('DBSubnetGroup'):
        logger.debug("Expected RDSInstance to have a DBSubnetGroup but it doesn't.  Here is the object: %s", instance)
    else:
        db_sng = instance.get('DBSubnetGroup')
        neo4j_session.run(
            attach_rds_to_subnet_group,
            DBSubnetGroupName=db_sng.get('DBSubnetGroupName'),
            VpcId=db_sng.get("VpcId", None),
            DBSubnetGroupDescription=db_sng.get('DBSubnetGroupDescription', None),
            DBSubnetGroupStatus=db_sng.get('SubnetGroupStatus', None),
            DBInstanceArn=instance.get('DBInstanceArn'),
            aws_update_tag=aws_update_tag
        )
        _attach_ec2_subnets_to_subnetgroup(neo4j_session, db_sng, aws_update_tag)


def _attach_ec2_subnets_to_subnetgroup(neo4j_session, db_subnet_group, aws_update_tag):
    """
    Attach EC2Subnets to the DB Subnet Group.

    From https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html:
    `Each DB subnet group should have subnets in at least two Availability Zones in a given region. When creating a DB
    instance in a VPC, you must select a DB subnet group. Amazon RDS uses that DB subnet group and your preferred
    Availability Zone to select a subnet and an IP address within that subnet to associate with your DB instance.`
    """
    attach_subnets_to_sng = """
    MATCH(subnet:EC2Subnet{subnetid:{SubnetIdentifier}}),
    (sng:DBSubnetGroup{id:{DBSubnetGroupName}})
    MERGE(sng)-[r:RESOURCE]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag},
    subnet.availability_zone = {SubnetAvailabilityZone}
    """
    # TODO: Note: RDS data has subnet availability zone data, but I don't think that this is the right place to
    # TODO: update it.  We should update the availability zone data in the EC2 ingestion part.
    if not db_subnet_group.get('DBSubnetGroupName'):
        logger.debug("Expected DBSubnetGroup to have a DBSubnetGroupName but it doesn't.  Here is the object: %s",
                     db_subnet_group)
    else:
        for sn in db_subnet_group.get('Subnets', []):
            subnet_id = sn.get('SubnetIdentifier', None)
            if not subnet_id:
                logger.debug("Expected Subnet to have a SubnetIdentifier but it doesn't. Here is the object: %s",
                             db_subnet_group)
            else:
                neo4j_session.run(
                    attach_subnets_to_sng,
                    SubnetIdentifier=subnet_id,
                    DBSubnetGroupName=db_subnet_group.get('DBSubnetGroupName'),
                    aws_update_tag=aws_update_tag,
                    SubnetAvailabilityZone=sn.get('SubnetAvailabilityZone', {}).get('Name', None)
                )


def _attach_ec2_security_groups(neo4j_session, instance, aws_update_tag):
    """
    Attach an RDS instance to its EC2SecurityGroups
    """
    attach_rds_to_group = """
    MATCH (rds:RDSInstance{id:{RdsArn}}),
    (sg:EC2SecurityGroup{groupid:{GroupId}})
    MERGE (rds)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {aws_update_tag}
    """
    if not instance.get('DBInstanceArn'):
        logger.debug("Expected RDSInstance to have a DBInstanceArn but it doesn't.  Here is the object: %r", instance)
    else:
        for group in instance.get('VpcSecurityGroups', []):
            neo4j_session.run(
                attach_rds_to_group,
                RdsArn=instance.get('DBInstanceArn'),
                GroupId=group.get('VpcSecurityGroupId'),
                aws_update_tag=aws_update_tag
            )


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
        if not replica.get('ReadReplicaSourceDBInstanceIdentifier'):
            logger.debug("Expected RDSInstance to be a read replica but its ReadReplicaSourceDBInstanceIdentifier "
                         "field is None.  Here is the object: %r", replica)
        elif not replica.get('DBInstanceArn'):
            logger.debug("Expected RDSInstance to have a DBInstanceArn but it doesn't."
                         "Here is the object: %r", replica)
        else:
            neo4j_session.run(
                attach_replica_to_source,
                ReplicaArn=replica['DBInstanceArn'],
                SourceInstanceIdentifier=replica['ReadReplicaSourceDBInstanceIdentifier'],
                aws_update_tag=aws_update_tag
            )


def _validate_rds_endpoint(rds):
    """
    Get Endpoint from RDS data structure.  Log to debug if an Endpoint field does not exist.
    """
    ep = rds.get('Endpoint', {})
    if not ep:
        logger.debug("RDS instance does not have an Endpoint field.  Here is the object: %r", rds)
    return ep


def cleanup_rds_instances(neo4j_session, common_job_parameters):
    """
    Remove RDS graph nodes that were created from other ingestion runs
    """
    run_cleanup_job('aws_import_rds_instances_cleanup.json', neo4j_session, common_job_parameters)


def sync_rds_instances(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
                       common_job_parameters):
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info("Syncing RDS for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_rds_instance_data(boto3_session, region)
        load_rds_instances(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_rds_instances(neo4j_session, common_job_parameters)

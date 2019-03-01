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
    rds.backup_retention_period = {BackupRetentionPeriod}
    WITH rds
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(rds)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for rds in data.get('DBInstances', []):
        instance_create_time = str(rds['InstanceCreateTime']) if 'InstanceCreateTime' in rds else None
        latest_restorable_time = str(rds['LatestRestorableTime']) if 'LatestRestorableTime' in rds else None
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
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag
        )


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

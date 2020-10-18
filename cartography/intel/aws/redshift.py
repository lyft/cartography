import logging

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_redshift_cluster_data(boto3_session, region):
    client = boto3_session.client('redshift', region_name=region)
    paginator = client.get_paginator('describe_clusters')
    clusters = []
    for page in paginator.paginate():
        clusters.extend(page['Clusters'])
    return clusters


def _make_redshift_cluster_arn(region, aws_account_id, cluster_identifier):
    """Cluster ARN format: https://docs.aws.amazon.com/redshift/latest/mgmt/redshift-iam-access-control-overview.html"""
    return f'arn:aws:redshift:{region}:{aws_account_id}:cluster:{cluster_identifier}'


def transform_redshift_cluster_data(clusters, region, current_aws_account_id):
    for cluster in clusters:
        cluster['arn'] = _make_redshift_cluster_arn(region, current_aws_account_id, cluster["ClusterIdentifier"])
        cluster['ClusterCreateTime'] = str(cluster['ClusterCreateTime']) if 'ClusterCreateTime' in cluster else None


@timeit
def load_redshift_cluster_data(neo4j_session, clusters, region, current_aws_account_id, aws_update_tag):
    ingest_cluster = """
    MERGE (cluster:RedshiftCluster{id: {Arn}})
    ON CREATE SET cluster.firstseen = timestamp(),
    cluster.arn = {Arn}
    SET cluster.availability_zone = {AZ},
    cluster.cluster_create_time = {ClusterCreateTime},
    cluster.cluster_identifier = {ClusterIdentifier},
    cluster.cluster_revision_number = {ClusterRevisionNumber},
    cluster.db_name = {DBName},
    cluster.encrypted = {Encrypted},
    cluster.cluster_status = {ClusterStatus},
    cluster.endpoint_address = {EndpointAddress},
    cluster.endpoint_port = {EndpointPort},
    cluster.master_username = {MasterUsername},
    cluster.node_type = {NodeType},
    cluster.number_of_nodes = {NumberOfNodes},
    cluster.publicly_accessible = {PubliclyAccessible},
    cluster.vpc_id = {VpcId},
    cluster.lastupdated = {aws_update_tag},
    cluster.region = {Region}
    WITH cluster
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(cluster)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    for cluster in clusters:
        neo4j_session.run(
            ingest_cluster,
            Arn=cluster['arn'],
            AZ=cluster['AvailabilityZone'],
            ClusterCreateTime=cluster['ClusterCreateTime'],
            ClusterIdentifier=cluster['ClusterIdentifier'],
            ClusterRevisionNumber=cluster['ClusterRevisionNumber'],
            ClusterStatus=cluster['ClusterStatus'],
            DBName=cluster['DBName'],
            Encrypted=cluster['Encrypted'],
            EndpointAddress=cluster.get('Endpoint').get('Address'),
            EndpointPort=cluster.get('Endpoint').get('Port'),
            MasterUsername=cluster['MasterUsername'],
            NodeType=cluster['NodeType'],
            NumberOfNodes=cluster['NumberOfNodes'],
            PubliclyAccessible=cluster['PubliclyAccessible'],
            VpcId=cluster.get('VpcId'),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        _attach_ec2_security_groups(neo4j_session, cluster, aws_update_tag)
        _attach_iam_roles(neo4j_session, cluster, aws_update_tag)
        _attach_aws_vpc(neo4j_session, cluster, aws_update_tag)


@timeit
def _attach_ec2_security_groups(neo4j_session, cluster, aws_update_tag):
    attach_cluster_to_group = """
    MATCH (c:RedshiftCluster{id:{ClusterArn}})
    MERGE (sg:EC2SecurityGroup{id:{GroupId}})
    MERGE (c)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {aws_update_tag}
    """
    for group in cluster.get('VpcSecurityGroups', []):
        neo4j_session.run(
            attach_cluster_to_group,
            ClusterArn=cluster['arn'],
            GroupId=group['VpcSecurityGroupId'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_iam_roles(neo4j_session, cluster, aws_update_tag):
    attach_cluster_to_role = """
    MATCH (c:RedshiftCluster{id:{ClusterArn}})
    MERGE (p:AWSPrincipal{arn:{RoleArn}})
    MERGE (c)-[s:STS_ASSUMEROLE_ALLOW]->(p)
    ON CREATE SET s.firstseen = timestamp()
    SET s.lastupdated = {aws_update_tag}
    """
    for role in cluster.get('IamRoles', []):
        neo4j_session.run(
            attach_cluster_to_role,
            ClusterArn=cluster['arn'],
            RoleArn=role['IamRoleArn'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_aws_vpc(neo4j_session, cluster, aws_update_tag):
    attach_cluster_to_vpc = """
    MATCH (c:RedshiftCluster{id:{ClusterArn}})
    MERGE (v:AWSVpc{id:{VpcId}})
    MERGE (c)-[m:MEMBER_OF_AWS_VPC]->(v)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {aws_update_tag}
    """
    if cluster.get('VpcId'):
        neo4j_session.run(
            attach_cluster_to_vpc,
            ClusterArn=cluster['arn'],
            VpcId=cluster['VpcId'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_redshift_clusters_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_redshift_clusters(neo4j_session, boto3_session, region, current_aws_account_id, aws_update_tag):
    data = get_redshift_cluster_data(boto3_session, region)
    transform_redshift_cluster_data(data, region, current_aws_account_id)
    load_redshift_cluster_data(neo4j_session, data, region, current_aws_account_id, aws_update_tag)


@timeit
def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing Redshift clusters for region '%s' in account '%s'.", region, account_id)
        sync_redshift_clusters(neo4j_session, boto3_session, region, account_id, sync_tag)
    cleanup(neo4j_session, common_job_parameters)

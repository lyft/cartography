import time
import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_redshift_reserved_node(boto3_session: boto3.session.Session, region: str, current_aws_account_id: str) -> List[Dict]:
    try:
        client = boto3_session.client('redshift', region_name=region)
        paginator = client.get_paginator('describe_reserved_nodes')
        reserved_nodes: List = []
        for page in paginator.paginate():
            reserved_nodes.extend(page['ReservedNodes'])
        for reserved_node in reserved_nodes:
            reserved_node['region'] = region
            reserved_node['arn'] = f"arn:aws:redshift:{region}:{current_aws_account_id}:reserved-node/{reserved_node['ReservedNodeId']}"
            reserved_node['consolelink'] = aws_console_link.get_console_link(arn=reserved_node['arn'])
        return reserved_nodes

    except ClientError as e:
        logger.error(f'Failed to call redshift describe_reserved_nodes: {region} - {e}')
        return reserved_nodes


def load_redshift_reserved_node(session: neo4j.Session, reserved_nodes: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_redshift_reserved_node_tx, reserved_nodes, current_aws_account_id, aws_update_tag)


@timeit
def _load_redshift_reserved_node_tx(
    tx: neo4j.Transaction, data: List[Dict], current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_rds_secgroup = """
    UNWIND {reserved_nodes} as reserved_node
        MERGE (node:RedshiftReservedNode{id: reserved_node.arn})
        ON CREATE SET node.firstseen = timestamp(),
            node.arn = reserved_node.arn
        SET node.reserved_node_offering_id = reserved_node.ReservedNodeOfferingId,
            node.name = reserved_node.ReservedNodeId,
            node.reserved_node_id = reserved_node.ReservedNodeId,
            node.node_type = reserved_node.NodeType,
            node.start_time = reserved_node.StartTime,
            node.duration = reserved_node.Duration,
            node.fixed_price = reserved_node.FixedPrice,
            node.usage_price = reserved_node.UsagePrice,
            node.currency_code = reserved_node.CurrencyCode,
            node.node_count = reserved_node.NodeCount,
            node.state = reserved_node.State,
            node.offering_type = reserved_node.OfferingType,
            node.reserved_node_offering_type = reserved_node.ReservedNodeOfferingType,
            node.lastupdated = {aws_update_tag}
        WITH node
        MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (aa)-[r:RESOURCE]->(node)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        ingest_rds_secgroup,
        reserved_nodes=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


def cleanup_redshift_reserved_node(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_redshift_reserved_nodes_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_redshift_reserved_node(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        logger.info("Syncing redshift_reserved_node for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_redshift_reserved_node(boto3_session, region, current_aws_account_id))

    logger.info(f"Total Redshift Reserved Nodes: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('redshift', None):
        pageNo = common_job_parameters.get("pagination", {}).get("redshift", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("redshift", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for redshift_reserved_node {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('redshift', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('redshift', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('redshift', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['redshift']['hasNextPage'] = has_next_page

    load_redshift_reserved_node(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_redshift_reserved_node(neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_redshift_cluster_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('redshift', region_name=region)
    paginator = client.get_paginator('describe_clusters')
    clusters: List[Dict] = []
    for page in paginator.paginate():
        clusters.extend(page['Clusters'])
    for cluster in clusters:
        cluster['region'] = region
    return clusters


def _make_redshift_cluster_arn(region: str, aws_account_id: str, cluster_identifier: str) -> str:
    """Cluster ARN format: https://docs.aws.amazon.com/redshift/latest/mgmt/redshift-iam-access-control-overview.html"""
    return f'arn:aws:redshift:{region}:{aws_account_id}:cluster:{cluster_identifier}'


def transform_redshift_cluster_data(clusters: List[Dict], current_aws_account_id: str) -> None:
    for cluster in clusters:
        cluster['arn'] = _make_redshift_cluster_arn(
            cluster['region'], current_aws_account_id, cluster["ClusterIdentifier"])
        cluster['ClusterCreateTime'] = str(cluster['ClusterCreateTime']) if 'ClusterCreateTime' in cluster else None


@timeit
def load_redshift_cluster_data(
    neo4j_session: neo4j.Session, clusters: List[Dict],
    current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_cluster = """
    MERGE (cluster:RedshiftCluster{id: {Arn}})
    ON CREATE SET cluster.firstseen = timestamp(),
    cluster.arn = {Arn}
    SET cluster.availability_zone = {AZ},
    cluster.cluster_create_time = {ClusterCreateTime},
    cluster.cluster_identifier = {ClusterIdentifier},
    cluster.cluster_revision_number = {ClusterRevisionNumber},
    cluster.db_name = {DBName},
    cluster.consolelink = {consolelink},
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
    # consolelink=aws_console_link.get_console_link(arn=cluster['arn']),

    for cluster in clusters:
        neo4j_session.run(
            ingest_cluster,
            Arn=cluster['arn'],
            consolelink='',
            AZ=cluster['AvailabilityZone'],
            ClusterCreateTime=cluster['ClusterCreateTime'],
            ClusterIdentifier=cluster['ClusterIdentifier'],
            ClusterRevisionNumber=cluster['ClusterRevisionNumber'],
            ClusterStatus=cluster['ClusterStatus'],
            DBName=cluster['DBName'],
            Encrypted=cluster['Encrypted'],
            EndpointAddress=cluster.get('Endpoint').get('Address'),    # type: ignore
            EndpointPort=cluster.get('Endpoint').get('Port'),   # type: ignore
            MasterUsername=cluster['MasterUsername'],
            NodeType=cluster['NodeType'],
            NumberOfNodes=cluster['NumberOfNodes'],
            PubliclyAccessible=cluster['PubliclyAccessible'],
            VpcId=cluster.get('VpcId'),
            Region=cluster['region'],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        _attach_ec2_security_groups(neo4j_session, cluster, aws_update_tag, current_aws_account_id)
        _attach_iam_roles(neo4j_session, cluster, aws_update_tag)
        _attach_aws_vpc(neo4j_session, cluster, aws_update_tag)


@timeit
def _attach_ec2_security_groups(neo4j_session: neo4j.Session, cluster: Dict, aws_update_tag: int, account_id: str) -> None:
    attach_cluster_to_group = """
    MATCH (c:RedshiftCluster{id:{ClusterArn}})
    MERGE (sg:EC2SecurityGroup{id:{GroupId}})
    SET sg.consolelink = {consolelink}
    MERGE (c)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = {aws_update_tag}
    """
    for group in cluster.get('VpcSecurityGroups', []):
        region = group.get('region', '')
        group_id = group["GroupId"]
        group_arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{group_id}"
        consolelink = aws_console_link.get_console_link(arn=group_arn)
        neo4j_session.run(
            attach_cluster_to_group,
            ClusterArn=cluster['arn'],
            consolelink = consolelink,
            GroupId=group['VpcSecurityGroupId'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_iam_roles(neo4j_session: neo4j.Session, cluster: Dict, aws_update_tag: int) -> None:
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
def _attach_aws_vpc(neo4j_session: neo4j.Session, cluster: Dict, aws_update_tag: int) -> None:
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
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_redshift_clusters_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_redshift_clusters(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: str,
    current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        data.extend(get_redshift_cluster_data(boto3_session, region))

    logger.info(f"Total Redshift Clusters: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('redshift', None):
        pageNo = common_job_parameters.get("pagination", {}).get("redshift", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("redshift", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for redshift cluster {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('redshift', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('redshift', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('redshift', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['redshift']['hasNextPage'] = has_next_page

    transform_redshift_cluster_data(data, current_aws_account_id)
    load_redshift_cluster_data(neo4j_session, data, current_aws_account_id, aws_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Redshift clusters for account '%s', at %s.", current_aws_account_id, tic)
    sync_redshift_clusters(neo4j_session, boto3_session, regions,
                           current_aws_account_id, update_tag, common_job_parameters)
    sync_redshift_reserved_node(neo4j_session, boto3_session, regions,
                                current_aws_account_id, update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Redshift clusters: {toc - tic:0.4f} seconds")

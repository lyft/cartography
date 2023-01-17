import logging
from dataclasses import dataclass
from string import Template
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from .util import get_botocore_config
from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import OtherRelationships
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import build_ingestion_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_vpcs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_vpcs()['Vpcs']


@timeit
@aws_handle_regions
def get_ec2_flow_logs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    flow_logs: List[Dict] = []
    paginator = client.get_paginator('describe_flow_logs')
    for page in paginator.paginate():
        flow_logs.extend(page['FlowLogs'])
    return flow_logs


def _get_cidr_association_statement(block_type: str) -> str:
    INGEST_CIDR_TEMPLATE = Template("""
    MATCH (vpc:AWSVpc{id: $VpcId})
    WITH vpc
    UNWIND $CidrBlock as block_data
        MERGE (new_block:$block_label{id: $VpcId + '|' + block_data.$block_cidr})
        ON CREATE SET new_block.firstseen = timestamp()
        SET new_block.association_id = block_data.AssociationId,
        new_block.cidr_block = block_data.$block_cidr,
        new_block.block_state = block_data.$state_name.State,
        new_block.block_state_message = block_data.$state_name.StatusMessage,
        new_block.lastupdated = $update_tag
        WITH vpc, new_block
        MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(new_block)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag""")

    BLOCK_CIDR = "CidrBlock"
    STATE_NAME = "CidrBlockState"

    # base label type. We add the AWS ipv4 or 6 depending on block type
    BLOCK_TYPE = "AWSCidrBlock"

    if block_type == "ipv6":
        BLOCK_CIDR = "Ipv6" + BLOCK_CIDR
        STATE_NAME = "Ipv6" + STATE_NAME
        BLOCK_TYPE = BLOCK_TYPE + ":AWSIpv6CidrBlock"
    elif block_type == "ipv4":
        BLOCK_TYPE = BLOCK_TYPE + ":AWSIpv4CidrBlock"
    else:
        raise ValueError(f"Unsupported block type specified - {block_type}")

    return INGEST_CIDR_TEMPLATE.safe_substitute(block_label=BLOCK_TYPE, block_cidr=BLOCK_CIDR, state_name=STATE_NAME)


@timeit
def load_cidr_association_set(
    neo4j_session: neo4j.Session, vpc_id: str, vpc_data: Dict, block_type: str,
    update_tag: int,
) -> None:
    ingest_statement = _get_cidr_association_statement(block_type)

    if block_type == "ipv6":
        data = vpc_data.get("Ipv6CidrBlockAssociationSet", [])
    else:
        data = vpc_data.get("CidrBlockAssociationSet", [])

    neo4j_session.run(
        ingest_statement,
        VpcId=vpc_id,
        CidrBlock=data,
        update_tag=update_tag,
    )


@timeit
def load_ec2_vpcs(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    update_tag: int,
) -> None:
    # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html
    # {
    #     "Vpcs": [
    #         {
    #             "VpcId": "vpc-a01106c2",
    #             "InstanceTenancy": "default",
    #             "Tags": [
    #                 {
    #                     "Value": "MyVPC",
    #                     "Key": "Name"
    #                 }
    #             ],
    #             "CidrBlockAssociations": [
    #                 {
    #                     "AssociationId": "vpc-cidr-assoc-a26a41ca",
    #                     "CidrBlock": "10.0.0.0/16",
    #                     "CidrBlockState": {
    #                         "State": "associated"
    #                     }
    #                 }
    #             ],
    #             "State": "available",
    #             "DhcpOptionsId": "dopt-7a8b9c2d",
    #             "CidrBlock": "10.0.0.0/16",
    #             "IsDefault": false
    #         }
    #     ]
    # }

    ingest_vpc = """
    MERGE (new_vpc:AWSVpc{id: $VpcId})
    ON CREATE SET new_vpc.firstseen = timestamp(), new_vpc.vpcid =$VpcId
    SET new_vpc.instance_tenancy = $InstanceTenancy,
    new_vpc.state = $State,
    new_vpc.is_default = $IsDefault,
    new_vpc.primary_cidr_block = $PrimaryCIDRBlock,
    new_vpc.dhcp_options_id = $DhcpOptionsId,
    new_vpc.region = $Region,
    new_vpc.lastupdated = $update_tag
    WITH new_vpc
    MATCH (awsAccount:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (awsAccount)-[r:RESOURCE]->(new_vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag"""

    for vpc in data:
        vpc_id = vpc["VpcId"]  # fail if not present

        neo4j_session.run(
            ingest_vpc,
            VpcId=vpc_id,
            InstanceTenancy=vpc.get("InstanceTenancy", None),
            State=vpc.get("State", None),
            IsDefault=vpc.get("IsDefault", None),
            PrimaryCIDRBlock=vpc.get("CidrBlock", None),
            DhcpOptionsId=vpc.get("DhcpOptionsId", None),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            update_tag=update_tag,
        )

        load_cidr_association_set(
            neo4j_session,
            vpc_id=vpc_id,
            block_type="ipv4",
            vpc_data=vpc,
            update_tag=update_tag,
        )

        load_cidr_association_set(
            neo4j_session,
            vpc_id=vpc_id,
            block_type="ipv6",
            vpc_data=vpc,
            update_tag=update_tag,
        )


@dataclass(frozen=True)
class FlowLogNodeProperties(CartographyNodeProperties):
    firstseen: PropertyRef = PropertyRef('firstseen')
    flow_log_status: PropertyRef = PropertyRef('FlowLogStatus')
    id: PropertyRef = PropertyRef('FlowLogId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    resource_id: PropertyRef = PropertyRef('ResourceId')


@dataclass(frozen=True)
class FlowLogToCloudTrailRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlowLog)-[:MONITORS]->(:AWSVpc)
class FlowLogToAWSVpc(CartographyRelSchema):
    target_node_label: str = 'AWSVpc'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('ResourceId')})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: FlowLogToCloudTrailRelProps = FlowLogToCloudTrailRelProps()


@dataclass(frozen=True)
class FlowLogSchema(CartographyNodeSchema):
    label: str = 'FlowLog'
    properties: FlowLogNodeProperties = FlowLogNodeProperties()
    other_relationships: Optional[OtherRelationships] = OtherRelationships([
        FlowLogToAWSVpc(),
    ])


@timeit
def load_ec2_flow_logs(
    neo4j_session: neo4j.Session,
    flow_logs: List[Dict],
    update_tag: int,
) -> None:
    logger.info("Loading %d flow logs into graph.", len(flow_logs))

    ingestion_query = build_ingestion_query(FlowLogSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        flow_logs,
        lastupdated=update_tag,
    )


@timeit
def cleanup_ec2_vpcs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_vpc_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_vpc(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 VPC for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_vpcs(boto3_session, region)
        load_ec2_vpcs(neo4j_session, data, region, current_aws_account_id, update_tag)

        flow_logs = get_ec2_flow_logs(boto3_session, region)
        load_ec2_flow_logs(neo4j_session, flow_logs, update_tag)
    cleanup_ec2_vpcs(neo4j_session, common_job_parameters)

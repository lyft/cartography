import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_vpc_peerings(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_vpc_peering_connections()['VpcPeeringConnections']


@timeit
def load_vpc_peerings(neo4j_session, data, region, aws_account_id, aws_update_tag):

    ingest_vpc_peerings = """
    UNWIND {vpc_peerings} AS vpc_peering

    MERGE (pcx:PeeringConnection:AWSPeeringConnection{id: vpc_peering.VpcPeeringConnectionId})
    ON CREATE SET pcx.firstseen = timestamp()
    SET pcx.lastupdated = {aws_update_tag},
    pcx.allow_dns_resolution_from_remote_vpc =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowDnsResolutionFromRemoteVpc,
    pcx.allow_egress_from_local_classic_link_to_remote_vpc =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowEgressFromLocalClassicLinkToRemoteVpc,
    pcx.allow_egress_from_local_vpc_to_remote_classic_link =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowEgressFromLocalVpcToRemoteClassicLink,
    pcx.requester_region = vpc_peering.RequesterVpcInfo.Region,
    pcx.accepter_region = vpc_peering.AccepterVpcInfo.Region,
    pcx.status_code = vpc_peering.Status.Code,
    pcx.status_message = vpc_peering.Status.Message

    MERGE (avpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId})
    ON CREATE SET avpc.firstseen = timestamp()
    SET avpc.lastupdated = {aws_update_tag}, avpc.vpcid = vpc_peering.AccepterVpcInfo.VpcId

    MERGE (rvpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId})
    ON CREATE SET rvpc.firstseen = timestamp()
    SET rvpc.lastupdated = {aws_update_tag}, rvpc.vpcid = vpc_peering.RequesterVpcInfo.VpcId

    MERGE (aaccount:AWSAccount{id: vpc_peering.AccepterVpcInfo.OwnerId})
    ON CREATE SET aaccount.firstseen = timestamp(), aaccount.foreign = true
    SET aaccount.lastupdated = {aws_update_tag}

    MERGE (raccount:AWSAccount{id: vpc_peering.RequesterVpcInfo.OwnerId})
    ON CREATE SET raccount.firstseen = timestamp(), raccount.foreign = true
    SET raccount.lastupdated = {aws_update_tag}


    """

    neo4j_session.run(
        ingest_vpc_peerings, vpc_peerings=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )

    ingest_accepter_vpc = """
    UNWIND {vpc_peerings} AS vpc_peering

    MATCH (pcx:PeeringConnection{id: vpc_peering.VpcPeeringConnectionId}),
        (vpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId})
    MERGE (pcx)-[r:ACCEPTER_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}

    WITH vpc_peering
    MATCH (avpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId}),
        (aaccount:AWSAccount{id: vpc_peering.AccepterVpcInfo.OwnerId})
    MERGE (aaccount)-[r:RESOURCE]->(avpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_accepter_vpc, vpc_peerings=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )

    ingest_requester_vpc = """
    UNWIND {vpc_peerings} AS vpc_peering

    MATCH (pcx:PeeringConnection{id: vpc_peering.VpcPeeringConnectionId}),
        (vpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId})
    MERGE (pcx)-[r:REQUESTER_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}

    WITH vpc_peering
    MATCH (rvpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId}),
        (raccount:AWSAccount{id: vpc_peering.RequesterVpcInfo.OwnerId})
    MERGE (raccount)-[r:RESOURCE]->(rvpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_requester_vpc, vpc_peerings=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )

    ingest_accepter_cidr = """
    UNWIND {vpc_peerings} AS vpc_peering
    UNWIND vpc_peering.AccepterVpcInfo.CidrBlockSet AS c_b

    MERGE (ac_b:AWSCidrBlock:AWSIpv4CidrBlock{id: vpc_peering.AccepterVpcInfo.VpcId + '|' + c_b.CidrBlock})
    ON CREATE SET ac_b.firstseen = timestamp()
    SET ac_b.lastupdated = {aws_update_tag}, ac_b.cidr_block  =  c_b.CidrBlock

    WITH vpc_peering, ac_b
    MATCH (pcx:PeeringConnection{id: vpc_peering.VpcPeeringConnectionId}), (cb:AWSCidrBlock{id: ac_b.id})
    MERGE (pcx)-[r:ACCEPTER_CIDR]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}

    WITH vpc_peering, ac_b
    MATCH (vpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId}), (cb:AWSCidrBlock{id: ac_b.id})
    MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_accepter_cidr, vpc_peerings=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )

    ingest_requester_cidr = """
    UNWIND {vpc_peerings} AS vpc_peering
    UNWIND vpc_peering.RequesterVpcInfo.CidrBlockSet AS c_b

    MERGE (rc_b:AWSCidrBlock:AWSIpv4CidrBlock{id: vpc_peering.RequesterVpcInfo.VpcId + '|' + c_b.CidrBlock})
    ON CREATE SET rc_b.firstseen = timestamp()
    SET rc_b.lastupdated = {aws_update_tag}, rc_b.cidr_block  =  c_b.CidrBlock

    WITH vpc_peering, rc_b
    MATCH (pcx:PeeringConnection{id: vpc_peering.VpcPeeringConnectionId}), (cb:AWSCidrBlock{id: rc_b.id})
    MERGE (pcx)-[r:REQUESTER_CIDR]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}

    WITH vpc_peering, rc_b
    MATCH (vpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId}), (cb:AWSCidrBlock{id: rc_b.id})
    MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_requester_cidr, vpc_peerings=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def cleanup_vpc_peerings(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_vpc_peering_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_vpc_peerings(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 VPC peering for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_vpc_peerings(boto3_session, region)
        load_vpc_peerings(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_vpc_peerings(neo4j_session, common_job_parameters)

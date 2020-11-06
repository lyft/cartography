import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_vpc_peering(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_vpc_peering_connections()['VpcPeeringConnections']


@timeit
def load_ec2_vpc_peering(neo4j_session, data, aws_update_tag):
    # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpc-peering-connections.html
    # {
    #     "VpcPeeringConnections": [
    #         {
    #             "Status": {
    #                 "Message": "Active",
    #                 "Code": "active"
    #             },
    #             "Tags": [
    #                 {
    #                     "Value": "Peering-1",
    #                     "Key": "Name"
    #                 }
    #             ],
    #             "AccepterVpcInfo": {
    #                 "OwnerId": "111122223333",
    #                 "VpcId": "vpc-1a2b3c4d",
    #                 "CidrBlock": "10.0.1.0/28"
    #             },
    #             "VpcPeeringConnectionId": "pcx-11122233",
    #             "RequesterVpcInfo": {
    #                 "PeeringOptions": {
    #                     "AllowEgressFromLocalVpcToRemoteClassicLink": false,
    #                     "AllowEgressFromLocalClassicLinkToRemoteVpc": false
    #                 },
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-123abc45",
    #                 "CidrBlock": "192.168.0.0/16"
    #             }
    #         },
    #         {
    #             "Status": {
    #                 "Message": "Pending Acceptance by 444455556666",
    #                 "Code": "pending-acceptance"
    #             },
    #             "Tags": [],
    #             "RequesterVpcInfo": {
    #                 "PeeringOptions": {
    #                     "AllowEgressFromLocalVpcToRemoteClassicLink": false,
    #                     "AllowEgressFromLocalClassicLinkToRemoteVpc": false
    #                 },
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-11aa22bb",
    #                 "CidrBlock": "10.0.0.0/28"
    #             },
    #             "VpcPeeringConnectionId": "pcx-abababab",
    #             "ExpirationTime": "2014-04-03T09:12:43.000Z",
    #             "AccepterVpcInfo": {
    #                 "OwnerId": "444455556666",
    #                 "VpcId": "vpc-33cc44dd"
    #             }
    #         }
    #     ]
    # }

    # We assume the accept data is already in the graph since we run after all AWS account in scope
    # We don't assume the requestor data is in the graph as it can be a foreign AWS account
    # IPV6 peering is not supported, we default to AWSIpv4CidrBlock
    #
    # We skip the region field here as we may not know which one it's related to in case of foreign VPC
    ingest_peering = """
    MATCH (accepter_block:AWSIpv4CidrBlock{id: {AccepterVpcId} + '|' + {AccepterCidrBlock}})
    WITH accepter_block
    MERGE (requestor_account:AWSAccount{id: {RequesterOwnerId}})
    ON CREATE SET requestor_account.firstseen = timestamp(), requestor_account.foreign = true
    SET requestor_account.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_account
    MERGE (requestor_vpc:AWSVpc{id: {RequestorVpcId}})
    ON CREATE SET requestor_vpc.firstseen = timestamp(), requestor_vpc.vpcid = {RequestorVpcId}
    SET requestor_vpc.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_account, requestor_vpc
    MERGE (requestor_account)-[resource:RESOURCE]->(requestor_vpc)
    ON CREATE SET resource.firstseen = timestamp()
    SET resource.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_vpc
    MERGE (requestor_block:AWSCidrBlock:AWSIpv4CidrBlock{id: {RequestorVpcId} + '|' + {RequestorVpcCidrBlock}})
    ON CREATE SET requestor_block.firstseen = timestamp(), requestor_block.cidr_block = {RequestorVpcCidrBlock}
    SET requestor_block.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_vpc, requestor_block
    MERGE (requestor_vpc)-[r:BLOCK_ASSOCIATION]->(requestor_block)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH accepter_block, requestor_block
    MERGE (accepter_block)<-[r2:VPC_PEERING]->(requestor_block)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.status_code = {StatusCode},
    r2.status_message = {StatusMessage},
    r2.connection_id = {ConnectionId},
    r2.expiration_time = {ExpirationTime},
    r2.lastupdated = {aws_update_tag}
    """

    ingest_peering_block = """
    MATCH (accepter_block:AWSIpv4CidrBlock{id: {AccepterVpcId} + '|' + {AccepterCidrBlock}}),
    (requestor_block:AWSCidrBlock:AWSIpv4CidrBlock{id: {RequestorVpcId} + '|' + {RequestorVpcCidrBlock}})
    MERGE (accepter_block)<-[r:VPC_PEERING]->(requestor_block)
    ON CREATE SET r.firstseen = timestamp()
    SET r.status_code = {StatusCode},
    r.status_message = {StatusMessage},
    r.connection_id = {ConnectionId},
    r.expiration_time = {ExpirationTime},
    r.lastupdated = {aws_update_tag}
    """
    for peering in data:
        if peering["Status"]["Code"] == "active":
            neo4j_session.run(
                ingest_peering,
                AccepterVpcId=peering["AccepterVpcInfo"]["VpcId"],
                AccepterCidrBlock=peering["AccepterVpcInfo"]["CidrBlock"],
                RequesterOwnerId=peering["RequesterVpcInfo"]["OwnerId"],
                RequestorVpcId=peering["RequesterVpcInfo"]["VpcId"],
                RequestorVpcCidrBlock=peering["RequesterVpcInfo"]["CidrBlock"],
                StatusCode=peering["Status"]["Code"],
                StatusMessage=peering["Status"]["Message"],
                ConnectionId=peering["VpcPeeringConnectionId"],
                ExpirationTime=peering.get("ExpirationTime", None),
                aws_update_tag=aws_update_tag,
            )

            for accepter_block in peering["AccepterVpcInfo"].get("CidrBlockSet", []):
                for requestor_block in peering["RequesterVpcInfo"].get("CidrBlockSet", []):
                    neo4j_session.run(
                        ingest_peering_block,
                        AccepterVpcId=peering["AccepterVpcInfo"]["VpcId"],
                        AccepterCidrBlock=accepter_block["CidrBlock"],
                        RequestorVpcId=peering["RequesterVpcInfo"]["VpcId"],
                        RequestorVpcCidrBlock=requestor_block["CidrBlock"],
                        StatusCode=peering["Status"]["Code"],
                        StatusMessage=peering["Status"]["Message"],
                        ConnectionId=peering["VpcPeeringConnectionId"],
                        ExpirationTime=peering.get("ExpirationTime", None),
                        aws_update_tag=aws_update_tag,
                    )


@timeit
def cleanup_ec2_vpc_peering(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_vpc_peering_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_vpc_peering(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.info("Syncing EC2 VPC peering for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_vpc_peering(boto3_session, region)
        load_ec2_vpc_peering(neo4j_session, data, aws_update_tag)
    cleanup_ec2_vpc_peering(neo4j_session, common_job_parameters)

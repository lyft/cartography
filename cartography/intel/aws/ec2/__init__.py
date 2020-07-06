import logging

from .auto_scaling_groups import sync_ec2_auto_scaling_groups
from .instances import sync_ec2_instances
from .key_pairs import sync_ec2_key_pairs
from .load_balancer_v2s import sync_load_balancer_v2s
from .load_balancers import sync_load_balancers
from .security_groups import sync_ec2_security_groupinfo
from .tgw import sync_transit_gateways
from .vpc import sync_vpc
from .vpc_peering import sync_vpc_peering
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_ec2_regions(boto3_session):
    client = boto3_session.client('ec2')
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]


@timeit
def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    logger.info("Syncing EC2 for account '%s'.", account_id)
    sync_vpc(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_security_groupinfo(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_key_pairs(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_instances(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_ec2_auto_scaling_groups(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_load_balancers(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_load_balancer_v2s(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_vpc_peering(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)
    sync_transit_gateways(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

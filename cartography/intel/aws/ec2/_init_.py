import logging

from intel.aws.ec2 import auto_scaling_groups
from intel.aws.ec2 import instances
from intel.aws.ec2 import key_pairs
from intel.aws.ec2 import load_balancers
from intel.aws.ec2 import security_groups
from intel.aws.ec2 import vpc
from intel.aws.ec2 import vpc_peering

logger = logging.getLogger(__name__)


def get_ec2_regions(boto3_session):
    client = boto3_session.client('ec2')
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]


def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    logger.info("Syncing EC2 for account '%s'.", account_id)

    modules = (vpc, security_groups, key_pairs, instances, auto_scaling_groups, load_balancers, vpc_peering)

    for module in modules:
        module.sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters)

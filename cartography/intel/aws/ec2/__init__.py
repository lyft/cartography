import logging

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_ec2_regions(boto3_session):
    client = boto3_session.client('ec2')
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]

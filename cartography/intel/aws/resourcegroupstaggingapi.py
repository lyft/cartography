import logging
from string import Template

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_tag_data(boto3_session, region):
    """
    Create boto3 client and retrieve tag data.
    """
    client = boto3_session.client('resourcegroupstaggingapi', region=region)
    paginator = client.get_paginator('get_resources')
    resources = []
    for page in paginator.paginate(
        # Only ingest tags for resources that Cartography supports.
        # This is just a starting list; there may be others supported by this API.
        ResourceTypeFilters = [
            # 'acm',
            # 'backup',
            # 'cloudfront',
            # 'cloudwatch',
            # 'datapipeline',
            'ec2',
            # 'elasticache',
            # 'elasticfilesystem',
            # 'elasticloadbalancing',
            # 'elasticmapreduce',
            'es',
            # 'events',
            # 'firehose',
            # 'kinesis',
            # 'lambda',
            'rds',
            # 'redshif$',
            's3',
            # 'sagemaker',
            # 'sqs',
            # 'transfer'
        ]
    ):
        resources.extend(page['ResourceTagMappingList'])
    return {'ResourceTagMappingList': resources}

def load_tag_data(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    INGEST_TAG_TEMPLATE = Template("""
    MATCH (resource:$resource_label{id:{ResourceId}})
    MERGE(aws_tag:AWSTag:Tag{id:{}})
    MERGE (resource)-[r:TAGGED]->(aws_tag)
    SET r.lastupdated = {UpdateTag}, r.first
    """)
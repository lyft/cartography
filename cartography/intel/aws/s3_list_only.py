import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.intel.aws.s3 import cleanup_s3_buckets, get_s3_bucket_list, load_s3_buckets

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing S3 for account '%s'.", current_aws_account_id)
    bucket_data = get_s3_bucket_list(boto3_session)

    load_s3_buckets(neo4j_session, bucket_data, current_aws_account_id, update_tag)
    cleanup_s3_buckets(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='S3Bucket',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

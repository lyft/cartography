import time
import logging
from typing import Dict
from typing import List
from botocore.exceptions import ClientError

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudwatch_alarm(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    alarms = []
    try:
        client = boto3_session.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            alarms.extend(page['MetricAlarms'])
        for alarm in alarms:
            alarm['region'] = region

        return alarms

    except ClientError as e:
        logger.error(f'Failed to call CloudWatch describe_alarms: {region} - {e}')
        return alarms


def load_cloudwatch_alarm(session: neo4j.Session, alarms: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_cloudwatch_alarm_tx, alarms, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudwatch_alarm_tx(tx: neo4j.Transaction, alarms: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (alarm:AWSCloudWatchAlarm{id: record.AlarmArn})
    ON CREATE SET alarm.firstseen = timestamp(),
        alarm.arn = record.AlarmArn
    SET alarm.lastupdated = {aws_update_tag},
        alarm.name = record.AlarmName,
        alarm.region = record.region,
        alarm.alarm_actions = record.AlarmActions,
        alarm.namespace = record.Namespace,
        alarm.period = record.Period,
        alarm.state_value = record.StateValue,
        alarm.statistic = record.Statistic,
        alarm.actions_enabled = record.ActionsEnabled,
        alarm.metric_name = record.MetricName
    WITH alarm
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(alarm)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=alarms,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudwatch_alarm(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudwatch_alarm_cleanup.json', neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_cloudwatch_flowlogs(boto3_session: boto3.session.Session, region: str, current_aws_account_id: str) -> List[Dict]:
    flowlogs = []
    try:
        client = boto3_session.client('ec2', region_name=region)
        paginator = client.get_paginator('describe_flow_logs')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            flowlogs.extend(page['FlowLogs'])

        for flowlog in flowlogs:
            flowlog['arn'] = f"arn:aws:ec2:{region}:{current_aws_account_id}:vcp-flow-log/{flowlog['FlowLogId']}"
            flowlog['region'] = region

        return flowlogs

    except ClientError as e:
        logger.error(f'Failed to call EC2 describe_flow_logs: {region} - {e}')
        return flowlogs


def load_cloudwatch_flowlogs(session: neo4j.Session, flowlogs: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_cloudwatch_flowlogs_tx, flowlogs, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudwatch_flowlogs_tx(tx: neo4j.Transaction, flowlogs: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (log:AWSCloudWatchFlowLog{id: record.arn})
    ON CREATE SET log.firstseen = timestamp(),
        log.arn = record.arn
    SET log.lastupdated = {aws_update_tag},
        log.name = record.FlowLogId,
        log.region = record.region,
        log.creation_time = record.CreationTime,
        log.deliver_logs_status = record.DeliverLogsStatus,
        log.flow_log_id = record.FlowLogId,
        log.flow_log_status = record.FlowLogStatus,
        log.log_group_name = record.LogGroupName,
        log.resource_id = record.ResourceId,
        log.log_destination_type = record.LogDestinationType
    WITH log
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(log)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=flowlogs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudwatch_flowlogs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudwatch_flowlog_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Cloudwatch for account '%s', at %s.", current_aws_account_id, tic)

    alarms = []
    flowlogs = []
    for region in regions:
        logger.info("Syncing Cloudwatch for region '%s' in account '%s'.", region, current_aws_account_id)

        alarms.extend(get_cloudwatch_alarm(boto3_session, region))
        flowlogs.extend(get_cloudwatch_flowlogs(boto3_session, region, current_aws_account_id))

    if common_job_parameters.get('pagination', {}).get('cloudwatch', None):
        pageNo = common_job_parameters.get("pagination", {}).get("cloudwatch", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("cloudwatch", None)["pageSize"]
        totalPages = len(alarms) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for cloudwatch alarms {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('cloudwatch', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('cloudwatch', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('cloudwatch', {})['pageSize']
        if page_end > len(alarms) or page_end == len(alarms):
            alarms = alarms[page_start:]

        else:
            has_next_page = True
            alarms = alarms[page_start:page_end]
            common_job_parameters['pagination']['cloudwatch']['hasNextPage'] = has_next_page

    load_cloudwatch_alarm(neo4j_session, alarms, current_aws_account_id, update_tag)

    cleanup_cloudwatch_alarm(neo4j_session, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('cloudwatch', None):
        pageNo = common_job_parameters.get("pagination", {}).get("cloudwatch", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("cloudwatch", None)["pageSize"]
        totalPages = len(flowlogs) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1

        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for cloudwatch flowlogs {pageNo}/{totalPages} pageSize is {pageSize}')

        page_start = (common_job_parameters.get('pagination', {}).get('cloudwatch', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('cloudwatch', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('cloudwatch', {})['pageSize']
        if page_end > len(flowlogs) or page_end == len(flowlogs):
            flowlogs = flowlogs[page_start:]

        else:
            has_next_page = True
            flowlogs = flowlogs[page_start:page_end]
            common_job_parameters['pagination']['cloudwatch']['hasNextPage'] = has_next_page

    load_cloudwatch_flowlogs(neo4j_session, flowlogs, current_aws_account_id, update_tag)

    cleanup_cloudwatch_flowlogs(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    print(f"Total Time to process cloudwatch: {toc - tic:0.4f} seconds")

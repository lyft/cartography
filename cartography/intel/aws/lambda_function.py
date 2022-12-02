import time
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple

import boto3
import botocore
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_lambda_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Create an Lambda boto3 client and grab all the lambda functions.
    """
    client = boto3_session.client('lambda', region_name=region)
    paginator = client.get_paginator('list_functions')
    lambda_functions = []
    for page in paginator.paginate():
        for each_function in page['Functions']:
            each_function['region'] = region
            each_function['consolelink'] = aws_console_link.get_console_link(arn=each_function['FunctionArn'])
            each_function['isPublicFacing'] = False
            if not each_function.get('VpcConfig', {}).get('VpcId'):
                each_function['isPublicFacing'] = True
            lambda_functions.append(each_function)
    return lambda_functions


@timeit
def load_lambda_functions(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_lambda_functions = """
    UNWIND $lambda_functions_list AS lf
    MERGE (lambda:AWSLambda{id: lf.FunctionArn})
    ON CREATE SET lambda.firstseen = timestamp()
    SET lambda.name = lf.FunctionName,
    lambda.arn = lf.FunctionArn,
    lambda.region = lf.region,
    lambda.modifieddate = lf.LastModified,
    lambda.runtime = lf.Runtime,
    lambda.isPublicFacing = lf.isPublicFacing,
    lambda.consolelink = lf.consolelink,
    lambda.description = lf.Description,
    lambda.timeout = lf.Timeout,
    lambda.memory = lf.MemorySize,
    lambda.codesize = lf.CodeSize,
    lambda.handler = lf.Handler,
    lambda.version = lf.Version,
    lambda.tracingconfigmode = lf.TracingConfig.Mode,
    lambda.revisionid = lf.RevisionId,
    lambda.state = lf.State,
    lambda.statereason = lf.StateReason,
    lambda.statereasoncode = lf.StateReasonCode,
    lambda.lastupdatestatus = lf.LastUpdateStatus,
    lambda.lastupdatestatusreason = lf.LastUpdateStatusReason,
    lambda.lastupdatestatusreasoncode = lf.LastUpdateStatusReasonCode,
    lambda.packagetype = lf.PackageType,
    lambda.signingprofileversionarn = lf.SigningProfileVersionArn,
    lambda.signingjobarn = lf.SigningJobArn,
    lambda.codesha256 = lf.CodeSha256,
    lambda.architectures = lf.Architectures,
    lambda.masterarn = lf.MasterArn,
    lambda.kmskeyarn = lf.KMSKeyArn,
    lambda.lastupdated = $aws_update_tag
    WITH lambda, lf
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(lambda)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    WITH lambda, lf
    MATCH (role:AWSPrincipal{arn: lf.Role})
    MERGE (lambda)-[r:STS_ASSUME_ROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_lambda_functions,
        lambda_functions_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
@aws_handle_regions
def get_function_aliases(lambda_function: Dict, client: botocore.client.BaseClient) -> List[Any]:
    aliases: List[Any] = []
    paginator = client.get_paginator('list_aliases')
    for page in paginator.paginate(FunctionName=lambda_function['FunctionName']):
        aliases.extend(page['Aliases'])

    return aliases


@timeit
@aws_handle_regions
def get_event_source_mappings(lambda_function: Dict, client: botocore.client.BaseClient) -> List[Any]:
    event_source_mappings: List[Any] = []
    paginator = client.get_paginator('list_event_source_mappings')
    for page in paginator.paginate(FunctionName=lambda_function['FunctionName']):
        event_source_mappings.extend(page['EventSourceMappings'])

    return event_source_mappings


@timeit
@aws_handle_regions
def get_lambda_function_details(
        boto3_session: boto3.session.Session, data: List[Dict],
) -> Generator[Any, Any, None]:
    for lambda_function in data:
        region = lambda_function['region']
        client = boto3_session.client('lambda', region_name=region)
        function_aliases = get_function_aliases(lambda_function, client)
        event_source_mappings = get_event_source_mappings(lambda_function, client)
        layers = lambda_function.get('Layers', [])
        yield lambda_function['FunctionArn'], function_aliases, event_source_mappings, layers, region


@timeit
def load_lambda_function_details(
        neo4j_session: neo4j.Session, lambda_function_details: List[Tuple[str, List[Dict], List[Dict], List[Dict]]],
        update_tag: int, current_aws_account_id: str,
) -> None:
    lambda_aliases: List[Dict] = []
    lambda_event_source_mappings: List[Dict] = []
    lambda_layers: List[Dict] = []
    for function_arn, aliases, event_source_mappings, layers, region in lambda_function_details:
        if len(aliases) > 0:
            for alias in aliases:
                alias['FunctionArn'] = function_arn
                function_name = function_arn.split(':')[-1]
                alias['region'] = region
                alias['consolelink'] = aws_console_link.get_console_link(arn=f"arn:aws:lambda::{current_aws_account_id}:alias/{function_name}")
            lambda_aliases.extend(aliases)
        if len(event_source_mappings) > 0:
            for event in event_source_mappings:
                alias['FunctionArn'] = function_arn
                function_name = function_arn.split(':')[-1]
                event['region'] = region
                event['consolelink'] = aws_console_link.get_console_link(arn=f"arn:aws:lambda::{current_aws_account_id}:event-source-mapping/{function_name}")
            lambda_event_source_mappings.extend(event_source_mappings)
        if len(layers) > 0:
            for layer in layers:
                layer['FunctionArn'] = function_arn
                function_name = function_arn.split(':')[-1]
                layer['consolelink'] = aws_console_link.get_console_link(arn=f"arn:aws:lambda::{current_aws_account_id}:layer/{function_name}")
                layer['region'] = region
            lambda_layers.extend(layers)

    _load_lambda_function_aliases(neo4j_session, lambda_aliases, update_tag)
    _load_lambda_event_source_mappings(neo4j_session, lambda_event_source_mappings, update_tag)
    _load_lambda_layers(neo4j_session, lambda_layers, update_tag)


@timeit
def _load_lambda_function_aliases(neo4j_session: neo4j.Session, lambda_aliases: List[Dict], update_tag: int) -> None:
    ingest_aliases = """
    UNWIND $aliases_list AS alias
    MERGE (a:AWSLambdaFunctionAlias{id: alias.AliasArn})
    ON CREATE SET a.firstseen = timestamp()
    SET a.aliasname = alias.Name,
    a.region = alias.region,
    a.functionversion = alias.FunctionVersion,
    a.description = alias.Description,
    a.consolelink = alias.consolelink,
    a.revisionid = alias.RevisionId,
    a.lastupdated = $aws_update_tag,
    a.arn = alias.AliasArn
    WITH a, alias
    MATCH (lambda:AWSLambda{id: alias.FunctionArn})
    MERGE (lambda)-[r:KNOWN_AS]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_aliases,
        aliases_list=lambda_aliases,
        aws_update_tag=update_tag,
    )


@timeit
def _load_lambda_event_source_mappings(
        neo4j_session: neo4j.Session, lambda_event_source_mappings: List[Dict], update_tag: int,
) -> None:
    ingest_esms = """
    UNWIND $esm_list AS esm
    MERGE (e:AWSLambdaEventSourceMapping{id: esm.EventSourceArn})
    ON CREATE SET e.firstseen = timestamp()
    SET e.batchsize = esm.BatchSize,
    e.startingposition = esm.StartingPosition,
    e.region = esm.region,
    e.startingpositiontimestamp = esm.StartingPositionTimestamp,
    e.parallelizationfactor = esm.ParallelizationFactor,
    e.maximumbatchingwindowinseconds = esm.MaximumBatchingWindowInSeconds,
    e.eventsourcearn = esm.EventSourceArn,
    e.UUID = esm.UUID,
    e.consolelink = esm.consolelink,
    e.lastmodified = esm.LastModified,
    e.lastprocessingresult = esm.LastProcessingResult,
    e.state = esm.State,
    e.maximumrecordage = esm.MaximumRecordAgeInSeconds,
    e.bisectbatchonfunctionerror = esm.BisectBatchOnFunctionError,
    e.maximumretryattempts = esm.MaximumRetryAttempts,
    e.tumblingwindowinseconds = esm.TumblingWindowInSeconds,
    e.lastupdated = $aws_update_tag,
    e.arn = esm.EventSourceArn
    WITH e, esm
    MATCH (lambda:AWSLambda{id: esm.FunctionArn})
    MERGE (lambda)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_esms,
        esm_list=lambda_event_source_mappings,
        aws_update_tag=update_tag,
    )


@timeit
def _load_lambda_layers(neo4j_session: neo4j.Session, lambda_layers: List[Dict], update_tag: int,) -> None:
    ingest_layers = """
    UNWIND $layers_list AS layer
    MERGE (l:AWSLambdaLayer{id: layer.Arn})
    ON CREATE SET l.firstseen = timestamp()
    SET l.codesize = layer.CodeSize,
    l.region = layer.region,
    l.name = layer.LayerName,
    l.consolelink = layer.consolelink,
    l.signingprofileversionarn  = layer.SigningProfileVersionArn,
    l.signingjobarn = layer.SigningJobArn,
    l.lastupdated = $aws_update_tag,
    l.arn = layer.Arn
    WITH l, layer
    MATCH (lambda:AWSLambda{id: layer.FunctionArn})
    MERGE (lambda)-[r:HAS]->(l)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_layers,
        layers_list=lambda_layers,
        aws_update_tag=update_tag,
    )


@timeit
def cleanup_lambda(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_lambda_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_lambda_functions(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    data = []
    for region in regions:
        logger.info("Syncing Lambda for region in '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_lambda_data(boto3_session, region))

    logger.info(f"Total Lambdas: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('lambda_function', None):
        pageNo = common_job_parameters.get("pagination", {}).get("lambda_function", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("lambda_function", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for lambda_function {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('lambda_function', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('lambda_function', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('lambda_function', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['lambda_function']['hasNextPage'] = has_next_page

    load_lambda_functions(neo4j_session, data, current_aws_account_id, aws_update_tag)
    lambda_function_details = get_lambda_function_details(boto3_session, data)
    load_lambda_function_details(neo4j_session, lambda_function_details, aws_update_tag, current_aws_account_id)

    cleanup_lambda(neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Lambda for account '%s', at %s.", current_aws_account_id, tic)

    sync_lambda_functions(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters,
    )

    toc = time.perf_counter()
    logger.info(f"Time to process Lambda: {toc - tic:0.4f} seconds")

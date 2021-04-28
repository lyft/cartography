import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple

import boto3
import neo4j
import botocore

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


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
            lambda_functions.append(each_function)
    return lambda_functions


@timeit
def load_lambda_functions(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingest_lambda_functions = """
    UNWIND {lambda_functions_list} AS lf
    MERGE (lambda:AWSLambda{id: lf.Arn})
    ON CREATE SET lambda.firstseen = timestamp()
    SET lambda.name = lf.LambdaName,
    lambda.modifieddate = lf.LastModified,
    lambda.runtime = lf.Runtime,
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
    lambda.lastupdated = {aws_update_tag}
    WITH lambda
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(lambda)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH lambda, lf
    MATCH (role:AWSPrincipal{arn: lf.Role})
    MERGE (lambda)-[r:STS_ASSUME_ROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_lambda_functions,
        lambda_functions_list=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_lambda(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_lambda_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_function_aliases(lambda_function: Dict, client: botocore.client.BaseClient) -> List[Any]:
    aliases: List[Any] = []
    paginator = client.get_paginator('list_aliases')
    for page in paginator.paginate(FunctionName=lambda_function['FunctionName']):
        aliases.extend(page['Aliases'])

    return aliases


@timeit
def get_lambda_function_details(
        boto3_session: boto3.session.Session, data: List[Dict], region: str
) -> Generator[Any, Any, Any]:
    client = boto3_session.client('lambda', region_name=region)
    for lambda_function in data:
        function_aliases = get_function_aliases(lambda_function, client)
        yield lambda_function['FunctionArn'], function_aliases


@timeit
def load_lambda_function_details(
        neo4j_session: neo4j.Session, lambda_function_details: List[Tuple[Any, Any, Any, Any]], update_tag: int,
) -> None:
    lambda_aliases: List[Dict] = []
    for function_arn, aliases in lambda_function_details:
        if len(aliases) > 0:
            for alias in aliases:
                alias['FunctionArn'] = function_arn
            lambda_aliases.extend(aliases)

    _load_lambda_function_aliases(neo4j_session, lambda_aliases, update_tag)


@timeit
def _load_lambda_function_aliases(neo4j_session: neo4j.Session, lambda_aliases: List[Dict], update_tag: int) -> None:
    ingest_aliases = """
    UNWIND {aliases_list} AS alias
    MERGE (a:AWSLambdaFunctionAlias{id: alias.AliasArn})
    ON CREATE SET a.firstseen = timestamp()
    SET a.aliasname = alias.Name,
    a.functionversion = alias.FunctionVersion,
    a.description = alias.Description,
    a.revisionid = alias.RevisionId,
    a.lastupdated = {aws_update_tag}
    WITH a, alias
    MATCH (lambda:AWSLambda{id: alias.FunctionArn})
    MERGE (lambda)-[r:KNOWN_AS]->(alias)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_aliases,
        aliases_list=lambda_aliases,
        aws_update_tag=update_tag,
    )


@timeit
def sync_lambda_functions(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing Lambda for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_lambda_data(boto3_session, region)
        load_lambda_functions(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
        lambda_function_details = get_lambda_function_details(boto3_session, data, region)
        load_lambda_function_details(neo4j_session, lambda_function_details, aws_update_tag)

    cleanup_lambda(neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    sync_lambda_functions(
        neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters,
    )

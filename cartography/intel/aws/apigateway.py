import json
import logging

from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_apigateway_rest_apis(boto3_session, region):
    client = boto3_session.client('apigateway', region_name=region)
    paginator = client.get_paginator('get_rest_apis')
    apis = []
    for page in paginator.paginate():
        apis.extend(page['items'])
    return apis


def transform_apigateway_rest_apis(apis, region, current_aws_account_id):
    for api in apis:
        api['CreatedDate'] = str(api['createdDate']) if 'createdDate' in api else None


@timeit
def get_rest_api_details(boto3_session, rest_apis, region):
    client = boto3_session.client('apigateway', region_name=region)
    for api in rest_apis:
        stages = get_rest_api_stages(api, client)
        certificate = get_rest_api_client_certificate(stages, client)  # clientcertificate id is given by the api stage
        resources = get_rest_api_resources(api, client)
        policy = get_rest_api_policy(api, client)
        yield api['id'], stages, certificate, resources, policy


@timeit
def get_rest_api_stages(api, client):
    try:
        stages = client.get_stages(restApiId=api['id'])
    except ClientError as e:
        logger.warning(f"Failed to retrieve Stages for Api Id - {api['id']} - {e}")
        raise

    return stages['item']


@timeit
def get_rest_api_client_certificate(stages, client):
    response = None

    for stage in stages:
        if 'clientCertificateId' in stage:
            try:
                response = client.get_client_certificate(clientCertificateId=stage['clientCertificateId'])
            except ClientError as e:
                logger.warning(f"Failed to retrive Client Certificate for Stage {stage['stageName']} - {e}")
                raise
        else:
            return None

    return response


@timeit
def get_rest_api_resources(api, client):
    resources = []
    paginator = client.get_paginator('get_resources')
    response_iterator = paginator.paginate(restApiId=api['id'])
    for page in response_iterator:
        resources.extend(page['items'])

    return resources


@timeit
def get_rest_api_policy(api, client):
    policy = api['policy'] if 'policy' in api and api['policy'] else None
    return policy


@timeit
def load_apigateway_rest_apis(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_rest_apis = """
    MERGE (rest_api:RestAPI{id:{RestApiId}})
    ON CREATE SET rest_api.id = {RestApiId},
    rest_api.firstseen = timestamp(),
    rest_api.createddate = {CreatedDate}
    SET rest_api.version = {Version},
    rest_api.minimumcompressionsize = {minimumCompressionSize},
    rest_api.disableexecuteapiendpoint = {disableExecuteApiEndpoint},
    rest_api.lastupdated = {aws_update_tag},
    rest_api.region = {Region}
    WITH rest_api
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(rest_api)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for api in data:
        neo4j_session.run(
            ingest_rest_apis,
            RestApiId=api['id'],
            CreatedDate=str(api['createdDate']),
            Version=api.get('version'),
            minimumCompressionSize=str(api.get('minimumCompressionSize')),
            # endpointConfiguration=api('endpointConfiguration'),
            disableExecuteApiEndpoint=str(api.get('disableExecuteApiEndpoint')),
            aws_update_tag=aws_update_tag,
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
        )


@timeit
def _load_apigateway_policies(neo4j_session, policies, update_tag):
    ingest_policies = """
    UNWIND {policies} as policy
    MATCH (r:RestAPI) where r.name = policy.api_id
    SET r.anonymous_access = (coalesce(r.anonymous_access, false) OR policy.internet_accessible),
    r.anonymous_actions = coalesce(r.anonymous_actions, []) + policy.accessible_actions,
    r.lastupdated = {UpdateTag}
    """

    neo4j_session.run(
        ingest_policies,
        policies=policies,
        UpdateTag=update_tag,
    )


def _set_default_values(neo4j_session, aws_account_id):
    set_defaults = """
    MATCH (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(restApi:RestAPI) where NOT EXISTS(restApi.anonymous_actions)
    SET restApi.anonymous_access = false, restApi.anonymous_actions = []
    """

    neo4j_session.run(
        set_defaults,
        AWS_ID=aws_account_id,
    )


@timeit
def _load_apigateway_stages(neo4j_session, stages, update_tag, api_id, certificates):
    ingest_stages = """
    MERGE (s:Stage{id: {StageName}})
    ON CREATE SET s.firstseen = timestamp(), s.createddate = {CreatedDate}
    SET s.deploymentid = {DeploymentId},
    s.clientcertificateid = {ClientCertificateId},
    s.cacheclusterenabled = {CacheClusterEnabled},
    s.cacheclusterstatus = {CacheClusterStatus},
    s.tracingenabled = {TracingEnabled},
    s.webaclarn = {WebAclArn},
    s.lastupdated = {UpdateTag}
    WITH s 
    MATCH (rest_api:RestAPI{id:{RestApiId}})
    MERGE (s)-[r:STAGE_OF]->(rest_api)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for stage in stages:
        neo4j_session.run(
            ingest_stages,
            StageName=stage['stageName'],
            CreatedDate=str(stage['createdDate']),
            DeploymentId=stage['deploymentId'],
            ClientCertificateId=stage.get('clientCertificateId'),
            CacheClusterEnabled=str(stage.get('cacheClusterEnabled')),
            CacheClusterStatus=stage.get('cacheClusterStatus'),
            TracingEnabled=str(stage.get('tracingEnabled')),
            WebAclArn=stage.get('webAclArn'),
            UpdateTag=update_tag,
            RestApiId=api_id
        )

        _load_apigateway_certificates(neo4j_session, certificates, update_tag, stage['stageName'])
        _load_stage_methodsettings(neo4j_session, stage, update_tag, api_id)


@timeit
def _load_stage_methodsettings(neo4j_session, stage, update_tag, api_id):
    ingest_methodsettings = """
    MERGE (m:MethodSettings{id: {SettingsKey}})
    ON CREATE SET m.firstseen = timestamp()
    SET m.metricsenabled = {MetricsEnabled},
    m.logginglevel = {LoggingLevel},
    m.datatraceenabled = {DataTraceEnabled},
    m.throttlingburstlimit = {ThrottlingBurstLimit},
    m.throttlingratelimit = {ThrottlingRateLimit},
    m.cachingenabled = {CachingEnabled},
    m.cachettlinseconds = {CacheTtlInSeconds},
    m.cacheDataEncrypted = {CacheDataEncrypted},
    m.requireauthorizationforcachecontrol = {RequireAuthorizationForCacheControl},
    m.unauthorizedcachecontrolheaderstrategy = {UnauthorizedCacheControlHeaderStrategy},
    m.lastupdated = {UpdateTag}
    WITH m
    MATCH (stage:Stage{id: {StageName}})
    MERGE (m)-[r:METHOD_SETTINGS_OF]->(stage)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for key, value in stage['methodSettings'].items():
        neo4j_session.run(
            ingest_methodsettings,
            SettingsKey=str(key),
            MetricsEnabled=str(value.get('metricsEnabled')),
            LoggingLevel=value.get('loggingLevel'),
            DataTraceEnabled=str(value.get('dataTraceEnabled')),
            ThrottlingBurstLimit=str(value.get('throttlingBurstLimit')),
            ThrottlingRateLimit=str(value.get('throttlingRateLimit')),
            CachingEnabled=str(value.get('cachingEnabled')),
            CacheTtlInSeconds=str(value.get('cacheTtlInSeconds')),
            CacheDataEncrypted=str(value.get('cacheDataEncrypted')),
            RequireAuthorizationForCacheControl=str(value.get('requireAuthorizationForCacheControl')),
            UnauthorizedCacheControlHeaderStrategy=value.get('unauthorizedCacheControlHeaderStrategy'),
            StageName=stage['stageName'],
            UpdateTag=update_tag
        )


@timeit
def _load_apigateway_certificates(neo4j_session, certificates, update_tag, stage_name):
    ingest_certificates = """
    MERGE (c:Certificate{id: {ClientCertificateId}})
    ON CREATE SET c.firstseen = timestamp(), c.createddate = {CreatedDate}
    SET c.lastupdated = {UpdateTag}, c.expirationdate = {ExpirationDate}
    WITH c
    MATCH (stage:Stage{id: {StageName}})
    MERGE (c)-[r:CERTIFICATE_OF]->(stage)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for certificate in certificates:
        neo4j_session.run(
            ingest_certificates,
            ClientCertificateId=certificate['clientCertificateId'],
            CreatedDate=str(certificate['createdDate']),
            ExpirationDate=str(certificate.get('expirationDate')),
            StageName=stage_name,
            UpdateTag=update_tag
        )


@timeit
def _load_apigateway_resources(neo4j_session, resources, update_tag, api_id):
    ingest_resources = """
    MERGE (s:Resource{id: {ResourceId}})
    ON CREATE SET s.firstseen = timestamp()
    SET s.path = {Path}, 
    s.pathpart = {PathPart}, 
    s.parentid = {ParentId},
    s.lastupdated ={UpdateTag}
    WITH s
    MATCH (rest_api:RestAPI{id:{RestApiId}})
    MERGE (s)-[r:REST_API_RESOURCE]->(rest_api)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {UpdateTag}
    """

    for resource in resources:
        neo4j_session.run(
            ingest_resources,
            ResourceId=resource['id'],
            Path=resource.get('path'),
            PathPart=resource.get('pathPart'),
            ParentId=resource.get('parentId'),
            RestApiId=api_id,
            UpdateTag=update_tag
        )


@timeit
def load_rest_api_details(neo4j_session, stages_certificate_resources, region, aws_account_id, update_tag):
    stages = []
    certificates = []
    resources = []
    policies = []
    apiId = ""
    for api_id, stage, certificate, resource, policy in stages_certificate_resources:
        apiId = api_id
        parsed_policy = parse_policy(api_id, policy)
        if parsed_policy is not None:
            policies.extend(parsed_policy)
        if len(stage) > 0:
            stages.extend(stage)
        if len(resource) > 0:
            resources.extend(resource)
        if certificate:
            certificates.extend(certificate)

    # cleanup existing properties
    run_cleanup_job(
        'aws_apigateway_details.json',
        neo4j_session,
        {'UPDATE_TAG': update_tag, 'AWS_ID': aws_account_id},
    )

    _load_apigateway_policies(neo4j_session, policies, update_tag)
    _load_apigateway_stages(neo4j_session, stages, update_tag, apiId, certificates)
    _load_apigateway_resources(neo4j_session, resources, update_tag, apiId)
    _set_default_values(neo4j_session, aws_account_id)


@timeit
def parse_policy(api_id, policy):
    if policy is not None:
        policy = Policy(json.loads(policy))
        if policy.is_internet_accessible():
            return {
                "api_id": api_id,
                "internet_accessible": True,
                "accessible_actions": list(policy.internet_accessible_actions())
            }
        else:
            return None
    else:
        return None


@timeit
def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_apigateway_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_apigateway_rest_apis(neo4j_session, boto3_session, region, current_aws_account_id, aws_update_tag):
    rest_apis = get_apigateway_rest_apis(boto3_session, region)
    transform_apigateway_rest_apis(rest_apis, region, current_aws_account_id)
    load_apigateway_rest_apis(neo4j_session, rest_apis, region, current_aws_account_id, aws_update_tag)

    stages_certificate_resources = get_rest_api_details(boto3_session, rest_apis, region)
    load_rest_api_details(neo4j_session, stages_certificate_resources, region, current_aws_account_id, aws_update_tag)


@timeit
def sync(neo4j_session, boto3_session, regions, account_id, sync_tag, common_job_parameters):
    for region in regions:
        logger.info(f"Syncing APIGateway Rest APIs for region '{region}' in account '{account_id}'.")
        sync_apigateway_rest_apis(neo4j_session, boto3_session, region, account_id, sync_tag)
    cleanup(neo4j_session, common_job_parameters)

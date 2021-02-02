import logging
import json

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

def get_apigateway_integration(export_swagger_json):
    apigateway_integration = []
    for path in export_swagger_json["paths"].keys():
        for path_type in export_swagger_json["paths"][path].keys():
            if export_swagger_json["paths"][path][path_type]["x-amazon-apigateway-integration"]["type"] == "aws_proxy":
                uri = export_swagger_json["paths"][path][path_type]["x-amazon-apigateway-integration"]["uri"]
                uri = uri.split('/')[-2]
                apigateway_integration.append(uri)
    return apigateway_integration


@timeit
@aws_handle_regions
def get_rest_apis(boto3_session, region):
    """
    Create an apigateway boto3 client and grab all the lambda functions.
    """
    client = boto3_session.client('apigateway', region_name=region)
    rest_apis = []
    paginator = client.get_paginator("get_rest_apis")
    for page in paginator.paginate():
        for item in page['items']:
            stages = client.get_stages(restApiId=item['id'])['item']
            for stage in stages:
                export_swagger_json = client.get_export(restApiId=item['id'], 
                stageName=stage['stageName'], exportType='swagger', parameters={'extensions': 'integrations'})
                export_swagger_json = json.loads(export_swagger_json['body'].read())
                stage['export_swagger_json'] = export_swagger_json
                stage['apigateway_integrations'] = get_apigateway_integration(export_swagger_json)
            item['stages'] = stages
            rest_apis.append(item)
    return rest_apis


@timeit
def load_rest_apis(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    api_gateway_query = """
    MERGE (ag:APIGateway{id: {Id}})
    ON CREATE SET ag.firstseen = timestamp()
    SET ag.name = {Name},
    ag.description = {Description},
    ag.protocol = 'REST',
    ag.created_date = {CreatedDate},
    ag.endpointConfiguration = {EndpointConfiguration},
    ag.lastupdated = {aws_update_tag},
    ag.region = {Region}
    WITH ag
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(ag)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """


    stage_query = """
    MERGE (ags:APIGatewayStage{id: {Id}})
    ON CREATE SET ags.firstseen = timestamp()
    SET ags.stage_name = {StageName},
    ags.deployment_id = {DeploymentId},
    ags.description = {Description},
    ags.export_swagger_json = {export_swagger_json},
    ags.created_date = {CreatedDate},
    ags.last_updated_date = {LastUpdatedDate},
    ags.lastupdated = {aws_update_tag}
    WITH ags
    MATCH (ag:APIGateway{id: {ApiGatewayId}})
    MERGE (ag)-[r:HAS_STAGE]->(ags)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH ags
    UNWIND {apigateway_integrations} as apigateway_integration
        MATCH (integration{id:apigateway_integration})
        MERGE (ags)-[r:HAS_APIGATEWAY_INTEGRATION]->(integration)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    for api_gateway in data:
        neo4j_session.run(
            api_gateway_query,
            Id=api_gateway['id'],
            Name=api_gateway['name'],
            Description=api_gateway.get('description',''),
            CreatedDate=api_gateway['createdDate'],
            EndpointConfiguration=str(api_gateway.get('endpointConfiguration','')),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        for stage in api_gateway['stages']:
            neo4j_session.run(
                stage_query,
                Id=api_gateway['id'] + '/' + stage['stageName'],
                StageName=stage['stageName'],
                DeploymentId=stage['deploymentId'],
                Description=stage.get('description',''),
                export_swagger_json=str(stage['export_swagger_json']),
                CreatedDate=stage['createdDate'],
                LastUpdatedDate=stage['lastUpdatedDate'],
                ApiGatewayId=api_gateway['id'],
                apigateway_integrations=stage['apigateway_integrations'],
                aws_update_tag=aws_update_tag,
            )



@timeit
def cleanup_api_gateway(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_api_gateway_cleanup.json', neo4j_session, common_job_parameters)




def sync(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.info("Syncing ApiGateway for region in '%s' in account '%s'.", region, current_aws_account_id)
        data = get_rest_apis(boto3_session, region)
        load_rest_apis(neo4j_session, data, region, current_aws_account_id, aws_update_tag)

    cleanup_api_gateway(neo4j_session, common_job_parameters)
    

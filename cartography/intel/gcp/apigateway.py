import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_apigateway_locations(apigateway: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of locations within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of locations
    """
    locations = []
    try:
        req = apigateway.projects().locations().list(name=f'projects/{project_id}')
        while req is not None:
            res = req.execute()
            if res.get('locations', []):
                for location in req['locations']:
                    location['project_id'] = project_id
                    location['id'] = location['name']
                    locations.append(location)
            req = apigateway.projects().locations().list_next(previous_request=req, previous_response=res)
        return locations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve locations on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_apis(apigateway: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of apis within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of apis
    """
    apis = []
    try:
        req = apigateway.project().locations().apis().list(parent=f'projects/{project_id}/locations/global')
        while req is not None:
            res = req.execute()
            if res.get('apis', []):
                for api in res['apis']:
                    api['project_id'] = project_id
                    api['id'] = api['name']
                    apis.append(api)
            req = apigateway.project().locations().apis().list_next(previous_request=req, previous_response=res)
        return apis
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve apis on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_api_configs(apigateway: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of apis configs within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of api configs.
    """
    api_configs = []
    try:
        req = apigateway.projects().locations().apis().configs().list(
            pparent=f'projects/{project_id}/locations/global/apis/*',
        )
        while req is not None:
            res = req.execute()
            if res.get('apiConfigs', []):
                for apiConfig in res['apiConfigs']:
                    apiConfig['api_id'] = f"projects/{project_id}/locations/global/apis/\
                        {apiConfig.get('name').split('/')[-3]}"
                    apiConfig['id'] = apiConfig['name']
                    apiConfig['project_id'] = project_id
                    api_configs.append(apiConfig)
            req = apigateway.projects().locations().apis().configs().list_next(
                previous_request=req,
                previous_response=res,
            )
        return api_configs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve apis configs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_gateways(apigateway: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of gateways within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of gateways.
    """
    gateways = []
    try:
        req = apigateway.projects().locations().gateways().list(parent=f'projects/{project_id}/locations/*')
        while req is not None:
            res = req.execute()
            if res.get('gateways', []):
                for gateway in res['gateways']:
                    gateway['id'] = gateway['name']
                    gateway['project_id'] = project_id
                    gateways.append(gateway)
            req = apigateway.projects().locations().gateways().list_next(previous_request=req, previous_response=res)
        return gateways
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve gateways on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_apigateway_locations(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_apigateway_locations_tx, data_list, project_id, update_tag)


@timeit
def load_apigateway_locations_tx(
    tx: neo4j.Transaction, locations: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        Ingest GCP Project Locations into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type locations: Dict
        :param locations: A GCP Project Locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_project_locations = """
    UNWIND {locations} as loc
    MERGE (location:GCPLocation{id:loc.id})
    ON CREATE SET
        location.firstseen = timestamp()
    SET
        location.name = loc.name,
        location.locationId = loc.locationId,
        location.displayName = loc.displayName,
        location.lastupdated = {gcp_update_tag}
    WITH location
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(location)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_project_locations,
        locations=locations,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_apigateway_locations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP Project Locations

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apigateway_locations_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_apis(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_apis_tx, data_list, project_id, update_tag)


@timeit
def load_apis_tx(tx: neo4j.Transaction, apis: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP APIs into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type apis: Dict
        :param apis: A list of GCP APIs

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_apis = """
    UNWIND {apis} as ap
    MERGE (api:GCPAPI{id:ap.id})
    ON CREATE SET
        api.firstseen = timestamp()
    SET
        api.name = ap.name,
        api.createTime = ap.createTime,
        api.updateTime = ap.updateTime,
        api.displayName = ap.displayName,
        api.managedService = ap.managedService,
        api.lastupdated = {gcp_update_tag}
    WITH api
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:HAS_API_ENABLED]->(api)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_apis,
        apis=apis,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_apis(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP APIs

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apis_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_api_configs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_api_configs_tx, data_list, project_id, update_tag)


@timeit
def load_api_configs_tx(tx: neo4j.Transaction, configs: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP API Configs into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type configs: Dict
        :param configs: A list of GCP API Configs

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_api_configs = """
    UNWIND {configs} as conf
    MERGE (config:GCPAPIConfig{id:conf.id})
    ON CREATE SET
        config.firstseen = timestamp()
    SET
        config.name = conf.name,
        config.createTime = conf.createTime,
        config.updateTime = conf.updateTime,
        config.displayName = conf.displayName,
        config.gatewayServiceAccount = conf.gatewayServiceAccount,
        config.serviceConfigId = conf.serviceConfigId,
        config.state = conf.state,
        config.lastupdated = {gcp_update_tag}
    WITH config,conf
    MATCH (api:GCPAPI{id:conf.api_id})
    MERGE (api)-[r:HAS_CONFIG]->(config)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_api_configs,
        configs=configs,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_configs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP API Configs

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_api_configs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_gateways(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_gateways_tx, data_list, project_id, update_tag)


@timeit
def load_gateways_tx(tx: neo4j.Transaction, gateways: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP API Gateways into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type gateways: Dict
        :param gateways: A list of GCP API Gateways

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_gateways = """
    UNWIND {gateways} as g
    MERGE (gateway:GCPAPIGateway{id:g.id})
    ON CREATE SET
        gateway.firstseen = timestamp()
    SET
        gateway.name = g.name,
        gateway.createTime = g.createTime,
        gateway.updateTime = g.updateTime,
        gateway.displayName = g.displayName,
        gateway.apiConfig = g.apiConfig,
        gateway.state = g.state,
        gateway.defaultHostname = g.defaultHostname,
        gateway.lastupdated = {gcp_update_tag}
    WITH gateway,g
    MATCH (apiconfig:GCPAPIConfig{id:g.apiConfig})
    MERGE (apiconfig)-[r:HAS_GATEWAY]->(gateway)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_gateways,
        gateways=gateways,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_gateways(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP API Gateways

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_api_gateways_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_apigateways(
    neo4j_session: neo4j.Session, apigateway: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
        Get GCP API Gateway Resources using the API Gateway resource object, ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type apigateway: The apigateway resource object created by googleapiclient.discovery.build()
        :param dns: The GCP apigateway resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    logger.info("Syncing DNS records for project %s.", project_id)
    # API Gateway Locations
    locations = get_apigateway_locations(apigateway, project_id)
    load_apigateway_locations(neo4j_session, locations, project_id, gcp_update_tag)
    # Cleanup Locations
    cleanup_apigateway_locations(neo4j_session, common_job_parameters)
    # API Gateway APIs
    apis = get_apis(apigateway, project_id)
    load_apis(neo4j_session, apis, project_id, gcp_update_tag)
    # Cleanup APIs
    cleanup_apis(neo4j_session, common_job_parameters)
    # API Gateway API Configs
    configs = get_api_configs(apigateway, project_id)
    load_api_configs(neo4j_session, configs, project_id, gcp_update_tag)
    # Cleanup API Gateway Configs
    cleanup_api_configs(neo4j_session, common_job_parameters)
    # API Gateway Gateways
    gateways = get_gateways(apigateway, project_id)
    load_gateways(neo4j_session, gateways, project_id, gcp_update_tag)
    # Cleanup API Gateway Gateways
    cleanup_api_gateways(neo4j_session, common_job_parameters)

import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from . import label
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
                for location in res['locations']:
                    location['project_id'] = project_id
                    location['id'] = location['locationId']
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
def get_apis(apigateway: Resource, project_id: str, locations: List[Dict]) -> List[Dict]:
    """
        Returns a list of apis within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type locations: List
        :param locations: Locations List

        :rtype: list
        :return: List of apis
    """
    apis = []
    try:
        for location in locations:
            req = apigateway.projects().locations().apis().list(parent=f"projects/{project_id}/locations/{location['id']}")
            while req is not None:
                res = req.execute()
                if res.get('apis', []):
                    for api in res['apis']:
                        api['project_id'] = project_id
                        api['id'] = api.get('name','').split('/')[-1]
                        x = api.get('name').split('/')
                        x = x[x.index('locations') + 1].split("-")
                        api['region'] = x[0]
                        if len(x) > 1:
                            api['region'] = f"{x[0]}-{x[1]}"
                        api['iam_policy'] = get_api_policy_users(apigateway,api,project_id)
                        apis.append(api)
                req = apigateway.projects().locations().apis().list_next(previous_request=req, previous_response=res)
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
def get_api_policy_users(apigateway: Resource, api: Dict,project_id: str) -> List[Dict]:
    """
        Returns a list of users attached to IAM policy of an API within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type api: Dict
        :param api: The Dict of API object

        :type project_id: str
        :param project_id: Current Google Project Id

        : type locations: List
        : param Location: List of locations

        :rtype: list
        :return: List of api iam policy users
    """
    try:
        iam_policy = apigateway.projects().locations().apis().getIamPolicy(\
            resource=api['id']).execute()
        bindings = iam_policy.get('bindings',[])
        api['iam_policy'] = []
        for binding in bindings:
            for member in binding['members']:
                if member.startswith('allUsers'):
                    api['iam_policy'].append('allUsers')
                elif member.startswith('allAuthenticatedUsers'):
                    api['iam_policy'].append('allAuthenticatedUsers')
        return api['iam_policy']
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of apis on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

@timeit
def get_api_configs(apigateway: Resource, project_id: str, apis: List[Dict]) -> List[Dict]:
    """
        Returns a list of apis configs within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type apis: List
        :param: apis: List of apis

        :rtype: list
        :return: List of api configs.
    """
    api_configs = []
    try:
        for api in apis:
            req = apigateway.projects().locations().apis().configs().list(
                parent=api['name'],
            )
            while req is not None:
                res = req.execute()
                if res.get('apiConfigs', []):
                    for apiConfig in res['apiConfigs']:
                        apiConfig['api_id'] = api['id']
                        apiConfig['id'] = apiConfig['name']
                        apiConfig['project_id'] = project_id
                        x = apiConfig.get('name').split('/')
                        x = x[x.index('locations') + 1].split("-")
                        apiConfig['region'] = x[0]
                        if len(x) > 1:
                            apiConfig['region'] = f"{x[0]}-{x[1]}"
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
def get_gateways(apigateway: Resource, project_id: str, locations: List[Dict]) -> List[Dict]:
    """
        Returns a list of gateways within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type locations: List
        :param locations: List of locations

        :rtype: list
        :return: List of gateways.
    """
    gateways = []
    try:
        for location in locations:
            req = apigateway.projects().locations().gateways().list(parent=f'projects/{project_id}/locations/{location["id"]}')
            while req is not None:
                res = req.execute()
                if res.get('gateways', []):
                    for gateway in res['gateways']:
                        gateway['id'] = gateway['name']
                        gateway['project_id'] = project_id
                        x = gateway.get('name').split('/')
                        x = x[x.index('locations') + 1].split("-")
                        gateway['region'] = x[0]
                        if len(x) > 1:
                            gateway['region'] = f"{x[0]}-{x[1]}"
                        gateway['iam_policy'] = get_api_gateway_policy_users(apigateway,gateway,project_id)
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
def get_api_gateway_policy_users(apigateway: Resource, gateways: Dict,project_id: str) -> List[Dict]:
    """
        Returns a list of users attached to IAM policy of an API Gateway within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type gateway: Dict
        :param gateway: The Dict of gateway object

        :type project_id: str
        :param project_id: Current Google Project Id

        : type locations: List
        : param Location: List of locations

        :rtype: list
        :return: List of api gateway iam policy users
    """
    try:
        for gateway in gateways:
            iam_policy = apigateway.projects().locations().gateways().getIamPolicy(\
                resource=gateway.get('name')).execute()
            bindings = iam_policy.get('bindings',[])
            gateway['iam_policy'] = []
            for binding in bindings:
                for member in binding['members']:
                    if member.startswith('allUsers'):
                        gateway['iam_policy'].append('allUsers')
                    elif member.startswith('allAuthenticatedUsers'):
                        gateway['iam_policy'].append('allAuthenticatedUsers')
        return gateway['iam_policy']
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of api gateway on project %s due to permissions issues. Code: %s, Message: %s"
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
        location.region = loc.locationId,
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
        api.region = ap.region,
        api.updateTime = ap.updateTime,
        api.displayName = ap.displayName,
        api.iam_policy = ap.iam_policy,
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
    run_cleanup_job('gcp_apigateway_apis_cleanup.json', neo4j_session, common_job_parameters)


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
        config.region = conf.region,
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
    run_cleanup_job('gcp_apigateway_configs_cleanup.json', neo4j_session, common_job_parameters)

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
        gateway.region = g.region,
        gateway.iam_policy = g.iam_policy,
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
    run_cleanup_job('gcp_apigateway_gateways_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
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
    label.sync_labels(neo4j_session, locations, gcp_update_tag, common_job_parameters)
    # API Gateway APIs
    apis = get_apis(apigateway, project_id)
    load_apis(neo4j_session, apis, project_id, gcp_update_tag)
    # Cleanup APIs
    cleanup_apis(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, apis, gcp_update_tag, common_job_parameters)
    # API Gateway API Configs
    configs = get_api_configs(apigateway, project_id)
    load_api_configs(neo4j_session, configs, project_id, gcp_update_tag)
    # Cleanup API Gateway Configs
    cleanup_api_configs(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, configs, gcp_update_tag, common_job_parameters)
    # API Gateway Gateways
    gateways = get_gateways(apigateway, project_id)
    load_gateways(neo4j_session, gateways, project_id, gcp_update_tag)
    # Cleanup API Gateway Gateways
    cleanup_api_gateways(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, gateways, gcp_update_tag, common_job_parameters)
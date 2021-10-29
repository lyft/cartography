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
def get_gcp_functions(function: Resource,project_id: str) -> List[Dict]:
    """
        Returns a list of functions for a given project.
        
        :type functions: Resource
        :param function: The function resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type region: string
        :param region: The region in which the function is defined

        :rtype: list
        :return: List of Functions
    """
    try:
        regions = []
        request = function.projects().locations().list(name = project_id)
        while request is not None:
            response = request.execute()
            for location in response['locations']:
                regions.append(location)
            request = function.projects().locations().list_next(previous_request=request, previous_response=response)
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Functions locations on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

    try:
        functions = []
        for region in regions:
            request = function.projects().locations().functions().list(parent=f"projects/{project_id}/locations/{region}")
            while request is not None:
                response = request.execute()
                for func in response['functions']:
                    func['id'] = f"projects/{project_id}/locations/{region}/functions/{func['name']}"
                    functions.append(func)
                request = function.projects().locations().functions().list_next(previous_request=request, previous_response=response)
        return functions
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Functions on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

@timeit
def load_functions(neo4j_session: neo4j.Session,functions: List[Resource],project_id: str,gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type function_resp: List
        :param fucntion_resp: A list GCP Functions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_functions = """
    UNWIND {functions} as func
    MERGE(function:GCPFunction:{id:func.id})
    ON CREATE SET
        function.firstseen = timestamp()
    SET
        function.name = func.name,
        function.description = func.description,
        function.status = func.status,
        function.entryPoint = func.entryPoint,
        function.runtime = func.runtime,
        function.timeout = func.timeout,
        function.availableMemoryMb = func.availableMemoryMb,
        function.serviceAccountEmail = func.serviceAccountEmail,
        function.updateTime = func.updateTime,
        function.versionId = func.versionId,
        funtion.network = func.network,
        function.maxInstances = func.maxInstances,
        function.vpcConnector = func.vpcConnector,
        function.vpcConnectorEgressSettings = func.vpcConnectorEgressSettings,
        function.ingressSettings = func.ingressSettings,
        function.buildWorkerPool = func.buildWorkerPool,
        function.buildId = func.buildId,
        fucntion.sourceToken = func.sourceToken,
        function.sourceArchiveUrl = func.sourceArchiveUrl
    WITH function, func
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(function)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    neo4j_session.run(
        ingest_functions,
        functions = functions,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )

@timeit
def cleanup_gcp_functions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Functions and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_function_cleanup.json', neo4j_session, common_job_parameters)

@timeit
def sync(
    neo4j_session: neo4j.Session, function: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict
) -> None:
    """
    Get GCP Cloud Fucntions using the Cloud Function resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type function: The GCP Cloud Function resource object created by googleapiclient.discovery.build()
    :param function: The GCP Cloud Function resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing GCP Cloud Functions for project %s.", project_id)
    #FUNCTIONS
    functions = get_gcp_functions(function,project_id)
    load_functions(functions,project_id,gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_functions(neo4j_session, common_job_parameters)
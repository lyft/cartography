import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource
from cartography.intel.aws.ecr import transform_ecr_repository_images

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
                    func['policies'] = get_function_policies(function, project_id)
                    functions.append(func)
                request = function.projects().locations().list_next(previous_request=request, previous_response=response)
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
def get_function_policies(function: Resource,project_id: str) -> List[Dict]:
    """
        Returns a list of Function IAM policies

        Returns a list of functions for a given project.
        
        :type functions: Resource
        :param function: The function resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type region: string
        :param region: The region in which the function is defined

        :rtype: list
        :return: List of Function IAM polcies
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
        policies = []
        for region in regions:
            request = function.projects().locations().functions().getIamPolicy(resource=f"projects/{project_id}/locations/{region}/functions/{function['name'].split('/')[::-1][0]}")
            while request is not None:
                response = request.execute()
                policies.append(response)
        return policies
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Function policies on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

@timeit
def get_pubsub_subscriptions(pubsub: Resource,function: Resource,project_id: str) -> List[Resource]:
    """
        Returns a list of subscriptions for the function for a given project.

        :type pubsub: resource
        :param pubsub: The pubsub resource created by googleapiclient.discovery.build()

        :type function: resource
        :param function: The function resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of subscriptions
    """
    try:
        function['subscriptions'] = []
        all_names = []
        if 'eventTrigger' in function:
            if function['eventTrigger']['eventType'].split('/')[-1] == 'topic.publish':
                topic = function['eventTrigger']['resource']
                response = pubsub.projects().topics().subscriptions().list(topic=f"projects/{project_id}/topics/{topic}").execute()
            if not response:
                return []
        all_names.extend(response['subscriptions'])
        while 'nextPageToken' in response:
            response = pubsub.projects().topics().subscriptions().list(topic=f"projects/{project_id}/topics/{topic}", pageToken=response['nextPageToken']).execute()
            all_names.extend(response['subscriptions'])
        for sub_name in all_names:
            request = pubsub.projects().subscriptions().get(subscription=f"projects/{project_id}/subscriptions/{sub_name}")
            while request is not None:
                response = request.execute()
                for subscription in response['subscriptions']:
                    function['subscriptions'].append(subscription)
        return function['subscriptions']
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Subscriptions on project %s due to permissions issues. Code: %s, Message: %s"
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
        :param fucntion_resp: A list of subscriptions for GCP Functions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_functions = """
    UNWIND {functions} as func
    MERGE(function:GCPFunction:{name:fun.name})
    ON CREATE SET
        function.firstseen = timestamp()
    SET
        function.name = fun.name,
        function.description = fun.description,
        function.status = fun.status,
        function.entryPoint = fun.entryPoint,
        function.runtime = fun.runtime,
        function.timeout = fun.timeout,
        function.availableMemoryMb = fun.availableMemoryMb,
        function.serviceAccountEmail = fun.serviceAccountEmail,
        function.updateTime = fun.updateTime,
        function.versionId = fun.versionId,
        funtion.network = fun.network,
        function.maxInstances = fun.maxInstances,
        function.vpcConnector = fun.vpcConnector,
        function.vpcConnectorEgressSettings = fun.vpcConnectorEgressSettings,
        function.ingressSettings = fun.ingressSettings,
        function.buildWorkerPool = fun.buildWorkerPool,
        function.buildId = fun.buildId,
        fucntion.sourceToken = fun.sourceToken,
        function.sourceArchiveUrl = fun.sourceArchiveUrl
    WITH function, fun
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(function)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    neo4j_session.run(
        ingest_functions,
        fun = functions,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )

@timeit
def load_function_policies(neo4j_session: neo4j.Session,policies: List[Dict],project_id: str,gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type policies_resp: List
        :param policies_resp: A list of subscriptions for GCP Function Subscriptions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with 
    """
    ingest_policies = """
    UNWIND {policies} as poli
    MERGE(policies:poli)
    ON CREATE SET
        policy.firstseen = timestamp()
    SET
        policy.etag = poli.etag,
        policy.version = poli.version
    WITH policy, poli
    MATCH (function:GCPFunction{name:{function.name}})
    MERGE (function)-[r:HAS_POLICY]->(policy)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    neo4j_session.run(
        ingest_policies,
        poli = policies,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )

@timeit
def load_subscriptions(neo4j_session: neo4j.Session,subscriptions: List[Resource],project_id: str,gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type subscription_resp: List
        :param subscription_resp: A list of subscriptions for GCP Function Subscriptions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with 
    """
    ingest_subscriptions = """
    UNWIND {subscriptions} as sub
    MERGE(subscription:GCPSubscription:{name:sub.name})
    ON CREATE SET
        subscription.firstseen = timestamp()
    SET
        subscription.name = sub.name,
        subscription.topic = sub.topic,
        subscription.ackDeadlineSeconds = sub.ackDeadlineSeconds,
        subscription.retainAckedMessages = sub.retainAckedMessages,
        subscription.messageRetentionDuration = sub.messageRetentionDuration,
        subscription.enableMessageOrdering = sub.enableMessageOrdering,
        subscription.detached = sub.detached,
        subscription.topicMessageRetentionDuration = sub.topicMessageRetentionDuration
    WITH subscription, sub
    MATCH (function:GCPFunction{name:{function.name}})
    MERGE (function)-[r:HAS_SUBSCRIPTION]->(subscription)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    neo4j_session.run(
        ingest_subscriptions,
        sub=subscriptions,
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
    neo4j_session: neo4j.Session, function: Resource,pubsub: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict
) -> None:
    """
    Get GCP DNS Zones and Resource Record Sets using the DNS resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type function: The GCP Cloud Function resource object created by googleapiclient.discovery.build()
    :param function: The GCP Cloud Function resource object

    :type pubsub: The GCP Cloud PubSub resource object created by googleapiclient.discovery.build()
    :param function: The GCP Cloud PubSub resource object

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
    functions = get_gcp_functions(function,project_id,function['locations'])
    load_functions(functions,project_id)
    #FUNCTION POLICIES
    policies = get_function_policies(function,project_id)
    load_function_policies(policies,project_id)
    # SUBSCRIPTIONS
    subscriptions = get_pubsub_subscriptions(pubsub,function, project_id)
    load_subscriptions(neo4j_session, subscriptions, project_id, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gcp_functions(neo4j_session, common_job_parameters)
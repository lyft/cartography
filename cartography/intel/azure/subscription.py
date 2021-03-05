import logging
from typing import Dict
from typing import List

from azure.mgmt.resource import SubscriptionClient
import neo4j

from . import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_all_azure_subscriptions(credentials: Credentials) -> List[Dict]:
    # Create the client
    client = SubscriptionClient(credentials.arm_credentials)

    # Get all the accessible subscriptions
    subs = list(client.subscriptions.list())

    if not subs:
        logger.warning('failed to fetch subscriptions for the credentials')
        raise Exception('The provided credentials do not have access to any subscriptions')

    subscriptions = []
    for sub in subs:
        subscriptions.append({
            'id': sub['id'],
            'subscriptionId': sub['subscriptionId'],
            'displayName': sub['displayName'],
            'state': sub['state']
        })

    return subscriptions


def get_current_azure_subscription(credentials: Credentials, subscription_id: str) -> List[Dict]:
    # Create the client
    client = SubscriptionClient(credentials.arm_credentials)

    # Get all the accessible subscriptions
    sub = client.subscriptions.get(subscription_id)
    print(sub)

    if not sub:
        raise Exception(f'The provided credentials do not have access to this subscription: {subscription_id}')

    return [{
            'id': sub.id,
            'subscriptionId': sub.subscription_id,
            'displayName': sub.display_name,
            'state': sub.state
            }]


def load_azure_subscriptions(neo4j_session: neo4j.Session, tenant_id: str, subscriptions: List[Dict], update_tag: int, common_job_parameters: Dict) -> None:
    query = """
    MERGE (at:AzureTenant{id: {TENANT_ID}})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = {update_tag}
    WITH at
    MERGE (as:AzureSubscription{id: {SUBSCRIPTION_ID}})
    ON CREATE SET as.firstseen = timestamp(), as.path = {SUBSCRIPTION_PATH}
    SET as.lastupdated = {update_tag}, as.name = {SUBSCRIPTION_NAME}, as.state = {SUBSCRIPTION_STATE}
    WITH as, at
    MERGE (at)-[r:RESOURCE]->(as)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag};
    """
    for sub in subscriptions:
        neo4j_session.run(
            query,
            TENANT_ID=tenant_id,
            SUBSCRIPTION_ID=sub['subscriptionId'],
            SUBSCRIPTION_PATH=sub['id'],
            SUBSCRIPTION_NAME=sub['displayName'],
            SUBSCRIPTION_STATE=sub['state'],
            update_tag=update_tag,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_subscriptions_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session: neo4j.Session, tenant_id: str, subscriptions: List[Dict], update_tag: int, common_job_parameters: Dict) -> None:
    load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

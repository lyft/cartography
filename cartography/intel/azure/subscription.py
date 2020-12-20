import logging

from azure.mgmt.resource import SubscriptionClient

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_all_azure_subscriptions(credentials):
    # Create the client
    client = SubscriptionClient(credentials.arm_credentials)

    # client._client.config.add_user_agent(get_user_agent())

    # Get all the accessible subscriptions
    subs = list(client.subscriptions.list())

    if not subs:
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


def get_current_azure_subscription(credentials, subscription_id):
    # Create the client
    client = SubscriptionClient(credentials.arm_credentials)

    # client._client.config.add_user_agent(get_user_agent())

    # Get all the accessible subscriptions
    sub = list(client.subscriptions.get(subscription_id))

    if not sub:
        raise Exception(f'The provided credentials do not have access to this subscription: {subscription_id}')

    return [{
            'id': sub['id'],
            'subscriptionId': sub['subscriptionId'],
            'displayName': sub['displayName'],
            'state': sub['state']
            }]


def load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters):
    query = """
    MERGE (at:AzureTenant{id: {TENANT_ID}})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = {azure_update_tag}
    WITH at
    MERGE (as:AzureSubscription{id: {SUBSCRIPTION_ID}})
    ON CREATE SET as.firstseen = timestamp(), as.path = {SUBSCRIPTION_PATH}
    SET as.lastupdated = {azure_update_tag}, as.name = {SUBSCRIPTION_NAME}, as.state = {SUBSCRIPTION_STATE}
    WITH as, at
    MERGE (at)-[r:RESOURCE]->(as)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag};
    """
    for sub in subscriptions:
        neo4j_session.run(
            query,
            TENANT_ID=tenant_id,
            SUBSCRIPTION_ID=sub['subscriptionId'],
            SUBSCRIPTION_PATH=sub['id'],
            SUBSCRIPTION_NAME=sub['displayName'],
            SUBSCRIPTION_STATE=sub['state'],
            azure_update_tag=azure_update_tag,
        )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters):
    load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

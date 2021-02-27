import logging

from azure.mgmt.resource import SubscriptionClient

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_all_azure_subscriptions(credentials):
    try:
        # Create the client
        client = SubscriptionClient(credentials.arm_credentials)

        # Get all the accessible subscriptions
        subs = list(lambda x: x.as_dict(), client.subscriptions.list())

        if not subs:
            raise Exception('The provided credentials do not have access to any subscriptions')

        return subs

    except Exception as e:
        logger.warning("Error while retrieving subscriptions - {}".format(e))
        return []


def get_current_azure_subscription(credentials, subscription_id):
    try:
        # Create the client
        client = SubscriptionClient(credentials.arm_credentials)

        s = client.subscriptions.get(subscription_id)

        # Get all the accessible subscriptions
        subs = [s.as_dict()]
        # subs = [s]

        if not subs:
            raise Exception('The provided credentials do not have access to this subscription')

        return subs

    except Exception as e:
        logger.warning("Error while retrieving subscription info - {}".format(e))
        return []


def load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters):
    query = """
    MERGE (at:AzureTenant{id: {tenantID}})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = {azure_update_tag}
    WITH at
    MERGE (as:AzureSubscription{id: {id}})
    ON CREATE SET as.firstseen = timestamp(), as.subscriptionid = {subscriptionID}
    SET as.lastupdated = {azure_update_tag}, as.name = {name},
    as.state = {state}, as.authorizationsource={authorizationSource}
    WITH as, at
    MERGE (at)-[r:RESOURCE]->(as)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {azure_update_tag};
    """
    for sub in subscriptions:
        neo4j_session.run(
            query,
            tenantID=tenant_id,
            id=sub['id'],
            subscriptionID=sub['subscription_id'],
            name=sub['display_name'],
            state=sub['state'],
            authorizationSource=sub['authorization_source'],
            azure_update_tag=azure_update_tag,
        )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('azure_subscriptions_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters):
    load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, azure_update_tag, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

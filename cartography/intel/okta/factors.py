# Okta intel module - Factors
import logging

from cartography.intel.okta import get_user_id_from_graph, get_okta_api_key

from okta import FactorsClient
from okta.framework.OktaError import OktaError

logger = logging.getLogger(__name__)


def _create_factor_client(okta_org):
    """
    Create Okta FactorsClient
    :param okta_org: Okta organization name
    :return: Instance of FactorsClient
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/FactorsClient.py
    factor_client = FactorsClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=get_okta_api_key(),
    )

    return factor_client


def _get_factor_for_user_id(factor_client, user_id):
    """
    Get factor for user from the Okta server
    :param factor_client: factor client
    :param user_id: user to fetch the data from
    :return: Array of dictionary containing factor properties
    """

    user_factors = []

    try:
        factor_results = factor_client.get_lifecycle_factors(user_id)
    except OktaError as okta_error:
        logger.debug(
            f"Unable to get factor for user id {user_id} with "
            f"error code {okta_error.error_code} with description {okta_error.error_summary}",
        )

        return []

    for current_factor in factor_results:
        factor_props = transform_okta_user_factor(current_factor)
        user_factors.append(factor_props)

    return user_factors


def transform_okta_user_factor(okta_factor_info):
    """
    Transform okta user factor into consumable data for the graph
    :param okta_factor_info: okta factor information
    :return: Dictionary of properties for the factor
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/factor/Factor.py
    factor_props = {}
    factor_props["id"] = okta_factor_info.id
    factor_props["factor_type"] = okta_factor_info.factorType
    factor_props["provider"] = okta_factor_info.provider
    factor_props["status"] = okta_factor_info.status
    if okta_factor_info.created:
        factor_props["created"] = okta_factor_info.created.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        factor_props["created"] = None

    if okta_factor_info.lastUpdated:
        factor_props["okta_last_updated"] = okta_factor_info.lastUpdated.strftime("%m/%d/%Y, %H:%M:%S")
    else:
        factor_props["okta_last_updated"] = None

    # we don't import Profile data into the graph due as it contains sensitive data
    return factor_props


def _load_user_factors(neo4j_session, user_id, factors, okta_update_tag):
    """
    Add user factors into the graph
    :param neo4j_session: session with the Neo4j server
    :param user_id: user to map factors to
    :param factors: factors to add
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest = """
    MATCH (user:OktaUser{id: {USER_ID}})
    WITH user
    UNWIND {FACTOR_LIST} as factor_data
    MERGE (new_factor:OktaUserFactor{id: factor_data.id})
    ON CREATE SET new_factor.firstseen = timestamp()
    SET new_factor.factor_type = factor_data.factor_type,
    new_factor.provider = factor_data.provider,
    new_factor.status = factor_data.status,
    new_factor.created = factor_data.created,
    new_factor.okta_last_updated = factor_data.okta_last_updated,
    new_factor.lastupdated = {okta_update_tag}
    WITH user, new_factor
    MERGE (user)-[r:FACTOR]->(new_factor)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        USER_ID=user_id,
        FACTOR_LIST=factors,
        okta_update_tag=okta_update_tag,
    )


def sync_users_factors(neo4j_session, okta_org_id, okta_update_tag):
    """
    Sync user factors
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    logger.debug("Syncing Okta User Factors")

    factor_client = _create_factor_client(okta_org_id)
    users = get_user_id_from_graph(neo4j_session, okta_org_id)

    for user_id in users:
        user_factors = _get_factor_for_user_id(factor_client, user_id)
        _load_user_factors(neo4j_session, user_id, user_factors, okta_update_tag)
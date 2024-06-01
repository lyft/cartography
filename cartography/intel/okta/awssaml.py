# Okta intel module - AWS SAML
import logging
import re
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.util import timeit


logger = logging.getLogger(__name__)


def _parse_regex(regex_string: str) -> str:
    return regex_string.replace("{{accountid}}", "P<accountid>").replace("{{role}}", "P<role>").strip()


def _get_account_and_role_name(okta_group_name: str, mapping_regex: str) -> tuple[str, str] | None:
    regex = _parse_regex(mapping_regex)
    matches = re.search(regex, okta_group_name)
    if matches:
        account_id = matches.group("accountid")
        role_slug = matches.group("role")
        return account_id, role_slug
    return None


def transform_okta_group_to_aws_role(group_id: str, group_name: str, mapping_regex: str) -> Optional[Dict]:
    account_and_role = _get_account_and_role_name(group_name, mapping_regex)
    if account_and_role:
        accountid = account_and_role[0]
        role = account_and_role[1]
        role_arn = f"arn:aws:iam::{accountid}:role/{role}"
        return {"groupid": group_id, "role": role_arn}
    return None


@timeit
def query_for_okta_to_aws_role_mapping(neo4j_session: neo4j.Session, mapping_regex: str) -> List[Dict]:
    """
    Query the graph for all groups associated with the amazon_aws application and map them to AWSRoles
    :param neo4j_session: session from the Neo4j server
    :param mapping_regex: the regex used by the organization to map groups to aws roles
    """
    query = "MATCH (app:OktaApplication{name:'amazon_aws'})--(group:OktaGroup) return group.id, group.name"

    group_to_role_mapping: List[Dict] = []
    has_results = False
    results = neo4j_session.run(query)

    for res in results:
        has_results = True
        # input: okta group id, okta group name. output: aws role arn.
        mapping = transform_okta_group_to_aws_role(res["group.id"], res["group.name"], mapping_regex)
        if mapping:
            group_to_role_mapping.append(mapping)

    if has_results and not group_to_role_mapping:
        logger.warn(
            "AWS Okta Application present, but no mappings were found. "
            "Please verify the mapping regex is correct",
        )

    return group_to_role_mapping


@timeit
def _load_okta_group_to_aws_roles(
    neo4j_session: neo4j.Session, group_to_role: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Add the ALLOWED_BY relationship between OktaGroups and the AWSRoles they enable
    :param neo4j_session: session with the Neo4j server
    :param group_to_role: the mapping between OktaGroups and the AWSRoles they allow access to
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """

    UNWIND $GROUP_TO_ROLE as app_data
    MATCH (role:AWSRole{arn: app_data.role})
    MATCH (group:OktaGroup{id: app_data.groupid})
    MERGE (role)<-[r:ALLOWED_BY]-(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    neo4j_session.run(
        ingest_statement,
        GROUP_TO_ROLE=group_to_role,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_human_can_assume_role(neo4j_session: neo4j.Session, okta_update_tag: int) -> None:
    """
    Add the CAN_ASSUME_ROLE relationship between Humans and the AWSRoles they can assume
    :param neo4j_session: session with the Neo4j server
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (role:AWSRole)<-[:ALLOWED_BY]-(:OktaGroup)<-[:MEMBER_OF_OKTA_GROUP]-(:OktaUser)-[:IDENTITY_OKTA]-(human:Human)
    MERGE (human)-[r:CAN_ASSUME_ROLE]->(role)
    SET r.lastupdated = $okta_update_tag
    """

    neo4j_session.run(
        ingest_statement,
        okta_update_tag=okta_update_tag,
    )


def get_awssso_okta_groups(neo4j_session: neo4j.Session) -> list[str]:
    """
    Return list of all Okta group ids tied to the Okta Application named "amazon_aws_sso".
    """
    query = """
    MATCH (g:OktaGroup)--(a:OktaApplication{name:"amazon_aws_sso"})
    RETURN g.id
    """
    return neo4j_session.read_transaction(read_list_of_values_tx, query)


def get_aws_sso_role_arn(okta_group_name: str, mapping_regex: str, neo4j_session: neo4j.Session) -> str | None:
    account_and_role = _get_account_and_role_name(okta_group_name, mapping_regex)
    if not account_and_role:
        return None
    account_id = account_and_role[0]
    role_name = account_and_role[1]

    # The associated SSO role will have a 'AWSReservedSSO' prefix and a hashed suffix -- we remove those.
    query = """
    MATCH (:AWSAccount{id:$account_id})-[:RESOURCE]->(role:AWSRole{path:"/aws-reserved/sso.amazonaws.com/"})
    WHERE SPLIT(role.name, '_')[1..-1][0] = $role_slug
    RETURN role.arn AS role_arn
    """
    return neo4j_session.read_transaction(read_single_value_tx, query, account_id=account_id, role_slug=role_name)


def query_for_okta_to_awssso_role_mapping(neo4j_session: neo4j.Session, mapping_regex: str) -> list[dict[str, str]]:
    """
    Inputs:
    - neo4j session
    - the okta group to aws role mapping regex as defined in cartography.config
    Output:
    - a list of dicts with keys `groupid` and `role_arn`
    """
    result = []
    okta_groups = get_awssso_okta_groups(neo4j_session)
    for group_id in okta_groups:
        role_name = get_aws_sso_role_arn(group_id, mapping_regex, neo4j_session)
        if role_name:
            result.append({'groupid': group_id, 'role_arn': role_name})
    return result


def _load_awssso_tx(tx: neo4j.Transaction, group_to_role: list[dict[str, str]], okta_update_tag: int) -> None:
    ingest_statement = """
    UNWIND $GROUP_TO_ROLE as app_data
        MATCH (role:AWSRole{arn: app_data.role_arn})
        MATCH (group:OktaGroup{id: app_data.groupid})
        MERGE (role)<-[r:ALLOWED_BY]-(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $okta_update_tag
    """
    tx.run(
        ingest_statement,
        GROUP_TO_ROLE=group_to_role,
        okta_update_tag=okta_update_tag,
    )


def _load_okta_group_to_awssso_roles(
        neo4j_session: neo4j.Session,
        group_to_role: list[dict[str, str]],
        okta_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_awssso_tx, group_to_role, okta_update_tag)


@timeit
def sync_okta_aws_saml(neo4j_session: neo4j.Session, mapping_regex: str, okta_update_tag: int) -> None:
    """
    Sync okta integration with saml. This will link OktaGroups to the AWSRoles they enable.
    This is for people who use the okta saml provider for AWS
    https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC
    If an organization does not use okta as a SAML provider for AWS the query will not return any results
    and nothing will be added to the graph
    :param mapping_regex: session from the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta api key
    :return: Nothing
    """
    logger.info("Syncing Okta SAML Integration")

    # Query for the aws application and its associated groups
    group_to_role_mapping = query_for_okta_to_aws_role_mapping(neo4j_session, mapping_regex)
    _load_okta_group_to_aws_roles(neo4j_session, group_to_role_mapping, okta_update_tag)
    _load_human_can_assume_role(neo4j_session, okta_update_tag)

    group_to_ssorole_mapping = query_for_okta_to_awssso_role_mapping(neo4j_session, mapping_regex)
    _load_okta_group_to_awssso_roles(neo4j_session, group_to_ssorole_mapping, okta_update_tag)

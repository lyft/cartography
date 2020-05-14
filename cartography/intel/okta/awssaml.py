# Okta intel module - AWS SAML
import logging
import re

from cartography.util import timeit


logger = logging.getLogger(__name__)


def _parse_regex(regex_string):
    return regex_string.replace("{{accountid}}", "P<accountid>").replace("{{role}}", "P<role>").strip()


@timeit
def transform_okta_group_to_aws_role(group_id, group_name, mapping_regex):
    regex = _parse_regex(mapping_regex)
    matches = re.search(regex, group_name)
    if matches:
        accountid = matches.group("accountid")
        role = matches.group("role")
        role_arn = f"arn:aws:iam::{accountid}:role/{role}"
        return {"groupid": group_id, "role": role_arn}


@timeit
def query_for_okta_to_aws_role_mapping(neo4j_session, mapping_regex):
    """
    Query the graph for all groups associated with the amazon_aws application and map them to AWSRoles
    :param neo4j_session: session from the Neo4j server
    :param mapping_regex: the regex used by the organization to map groups to aws roles
    """
    query = "MATCH (app:OktaApplication{name:'amazon_aws'})--(group:OktaGroup) return group.id, group.name"

    group_to_role_mapping = []
    has_results = False
    results = neo4j_session.run(query)

    for res in results:
        has_results = True
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
def _load_okta_group_to_aws_roles(neo4j_session, group_to_role, okta_update_tag):
    """
    Add the ALLOWED_BY relationship between OktaGroups and the AWSRoles they enable
    :param neo4j_session: session with the Neo4j server
    :param group_to_role: the mapping between OktaGroups and the AWSRoles they allow access to
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """

    UNWIND {GROUP_TO_ROLE} as app_data
    MATCH (role:AWSRole{arn: app_data.role})
    MATCH (group:OktaGroup{id: app_data.groupid})
    MERGE (role)<-[r:ALLOWED_BY]-(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        GROUP_TO_ROLE=group_to_role,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_human_can_assume_role(neo4j_session, okta_update_tag):
    """
    Add the CAN_ASSUME_ROLE relationship between Humans and the AWSRoles they can assume
    :param neo4j_session: session with the Neo4j server
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (role:AWSRole)<-[:ALLOWED_BY]-(:OktaGroup)<-[:MEMBER_OF_OKTA_GROUP]-(:OktaUser)-[:IDENTITY_OKTA]-(human:Human)
    MERGE (human)-[r:CAN_ASSUME_ROLE]->(role)
    SET r.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest_statement,
        okta_update_tag=okta_update_tag,
    )


@timeit
def sync_okta_aws_saml(neo4j_session, mapping_regex, okta_update_tag):
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
    logger.debug("Syncing Okta SAML Integration")

    # Query for the aws application and its associated groups
    group_to_role_mapping = query_for_okta_to_aws_role_mapping(neo4j_session, mapping_regex)
    _load_okta_group_to_aws_roles(neo4j_session, group_to_role_mapping, okta_update_tag)
    _load_human_can_assume_role(neo4j_session, okta_update_tag)

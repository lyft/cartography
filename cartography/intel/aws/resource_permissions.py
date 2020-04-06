import logging
import re

import policyuniverse.statement

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)

# Overview of IAM in AWS
#

RESOURCE_PERMISSIONS_RELATIONSHIPS = [
    {
        "resource_type": "S3Bucket",
        "permissions": ["S3:GetObject"],
        "relationship_name": "CAN_READ",
    },
    {
        "resource_type": "S3Bucket",
        "permissions": ["S3:PutObject"],
        "relationship_name": "CAN_WRITE",
    },
    {
        "resource_type": "DynamoDBTable",
        "permissions": ["dynamodb:BatchGetItem", "dynamodb:GetItem", "dynamodb:GetRecords", "dynamodb:Query"],
        "relationship_name": "CAN_QUERY",
    }
    #,
    # {
    #     "resource_type": "AWSRole",
    #     "permissions": ["sts:AssumeRole"],
    #     "relationship_name": "STS_ASSUMEROLE_ALLOW",
    # },

]

def evaluate_clause(clause, match):
    clause = clause.replace("*", ".*")
    result = re.search(clause, match, flags=re.IGNORECASE)
    return not result is None

def evaluate_statment_clause_for_permission(statement, clause_name, match):
    if clause_name in statement:
        for clause in statement[clause_name]:
            if evaluate_clause(clause, match):
                return True
    return False


def evaluate_statements_for_permission(statements, permission, resource_arn):
    allowed = False
    for statement in statements:
        if evaluate_statment_clause_for_permission(statement, "action", permission):
            if not evaluate_statment_clause_for_permission(statement, "notaction", permission):
                if evaluate_statment_clause_for_permission(statement, "resource", resource_arn):
                    return True

    return allowed


def evaluate_policy_for_permission(statements, permissions, resource_arn):
    # AWS Policy evaluation reference
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html
    allow_statements = [s for s in statements if s["effect"] == "Allow"]
    deny_statements = [s for s in statements if s["effect"] == "Deny"]
    for permission in permissions:
        if not evaluate_statements_for_permission(deny_statements, permission, resource_arn):
            if evaluate_statements_for_permission(allow_statements, permission, resource_arn):
                return True
    return False


def parse_statement_node_group(node_group):
    return [n._properties for n in node_group]


def get_policies_for_account(neo4j_session, account_id):
    get_policy_query = """
    MATCH
    (acc:AWSAccount{id:{AccountId}})-[:RESOURCE]->
    (principal:AWSPrincipal)-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT policy.id AS policy_id,
    COLLECT(DISTINCT statements) AS statements
    """
    results = neo4j_session.run(
        get_policy_query,
        AccountId=account_id,
    )
    policies = {r["policy_id"]: parse_statement_node_group(r["statements"]) for r in results}
    return policies


def get_resource_arns(neo4j_session, account_id, node_label):
    get_resource_query = """
    MATCH (acc:AWSAccount{id:{AccountId}})-[:RESOURCE]->(resource:{NodeLabel})
    return resource.arn as arn
    """
    get_resource_query = get_resource_query.replace("{NodeLabel}", node_label)
    results = neo4j_session.run(
        get_resource_query,
        AccountId=account_id,
    )
    arns = [r["arn"] for r in results]
    return arns


def load_policy_mappings(neo4j_session, policy_mapping, node_type, relationship_name, update_tag):
    map_policy_query = """
    UNWIND {Mapping} as mapping
    MATCH (principal:AWSPrincipal)-[:POLICY]-> (policy:AWSPolicy{id:mapping.policy_id})
    MATCH (resource:{NodeType}{arn:mapping.resource_arn})
    MERGE (principal)-[r:{RelationshipName}]->(resource)
    SET r.lastupdated = {aws_update_tag}
    """
    if not policy_mapping:
        return
    map_policy_query = map_policy_query.replace("{NodeType}", node_type)
    map_policy_query = map_policy_query.replace("{RelationshipName}", relationship_name)
    neo4j_session.run(
        map_policy_query,
        Mapping=policy_mapping,
        aws_update_tag=update_tag,
    )


def sync(neo4j_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing Resource Permissions for account '%s'.", account_id)
    policies = get_policies_for_account(neo4j_session, account_id)

    for rpr in RESOURCE_PERMISSIONS_RELATIONSHIPS:
        resource_arns = get_resource_arns(neo4j_session, account_id, rpr["resource_type"])
        for policy_id, statements in policies.items():
            policy_mapping = []
            for resource_arn in resource_arns:
                if evaluate_policy_for_permission(statements, rpr["permissions"], resource_arn):
                    policy_mapping.append({"policy_id": policy_id, "resource_arn": resource_arn})
            load_policy_mappings(neo4j_session, policy_mapping, rpr["resource_type"], rpr["relationship_name"], update_tag)

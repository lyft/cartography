import logging
import re
import yaml
import policyuniverse.statement
import os
from cartography.util import run_cleanup_job
from cartography.graph.statement import GraphStatement
logger = logging.getLogger(__name__)

# Overview of IAM in AWS
#


def evaluate_clause(clause, match):
    clause = clause.replace("*", ".*")
    result = re.fullmatch(clause, match, flags=re.IGNORECASE)
    return not result is None


def evaluate_statment_clause_for_permission(statement, clause_name, match, missing_clause_return=False):
    if not clause_name in statement:
        return missing_clause_return
    for clause in statement[clause_name]:
        if evaluate_clause(clause, match):
            return True
    return False


def evaluate_statements_for_permission(statements, permission, resource_arn):
    allowed = False
    for statement in statements:
        if evaluate_statment_clause_for_permission(statement, "action", permission, missing_clause_return=True):
            if not evaluate_statment_clause_for_permission(statement, "notaction", permission):
                if evaluate_statment_clause_for_permission(statement, "resource", resource_arn):
                    if not evaluate_statment_clause_for_permission(statement, "notresource", resource_arn):
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


def cleanup_rpr(neo4j_session, node_type, relationship_name, update_tag, current_aws_id):
    cleanup_rpr_query = """
        MATCH (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(principal:AWSPrincipal)-[r:{RelationshipName}]->(resource:{NodeType}) 
        WHERE r.lastupdated <> {UPDATE_TAG} WITH r LIMIT {LIMIT_SIZE}  DELETE (r) return COUNT(*) as TotalCompleted
    """
    cleanup_rpr_query = cleanup_rpr_query.replace("{NodeType}", node_type)
    cleanup_rpr_query = cleanup_rpr_query.replace("{RelationshipName}", relationship_name)

    statement = GraphStatement(cleanup_rpr_query, {'UPDATE_TAG': update_tag, 'AWS_ID': current_aws_id}, True, 1000)
    statement.run(neo4j_session)


def parse_permission_relationship_file(file):
    if not os.path.isabs(file):
        file = os.path.join(os.getcwd(), file)
    with open(file) as f:
        relationship_mapping = yaml.load(f)
    return relationship_mapping


def sync(neo4j_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing Permission Relationships for account '%s'.", account_id)
    policies = get_policies_for_account(neo4j_session, account_id)
    relationship_mapping = parse_permission_relationship_file(common_job_parameters["permission_relationship_file"])
    for rpr in relationship_mapping:
        resource_arns = get_resource_arns(neo4j_session, account_id, rpr["target_label"])
        for policy_id, statements in policies.items():
            policy_mapping = []
            for resource_arn in resource_arns:
                if evaluate_policy_for_permission(statements, rpr["permissions"], resource_arn):
                    policy_mapping.append({"policy_id": policy_id, "resource_arn": resource_arn})
            load_policy_mappings(neo4j_session, policy_mapping,
                                 rpr["target_label"], rpr["relationship_name"], update_tag)
        cleanup_rpr(neo4j_session, rpr["target_label"], rpr["relationship_name"], update_tag, account_id)

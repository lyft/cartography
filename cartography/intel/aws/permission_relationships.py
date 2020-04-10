import logging
import yaml
import policyuniverse.statement
import os
import fnmatch
from cartography.util import run_cleanup_job
from cartography.graph.statement import GraphStatement
logger = logging.getLogger(__name__)


def evaluate_clause(clause, match):
    # AWS [not]actions and [not]resources can use linux style wildcards *
    # fnmatch does not do a true case insensitive match, so we must convert the inputs
    return fnmatch.fnmatch(match.lower(), clause.lower())


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
    # returns (allowed_by_policy, explicitly_denied_by_policy)
    # return cases
    # (True, False) - The policy allows the action
    # (False, False) - The poliy does not allow the action, but also doesn't explicitly deny it
    # (False, True) - The policy specifically denies the action. There is no need to evaluate other policies

    allow_statements = [s for s in statements if s["effect"] == "Allow"]
    deny_statements = [s for s in statements if s["effect"] == "Deny"]
    for permission in permissions:
        if evaluate_statements_for_permission(deny_statements, permission, resource_arn):
            return False, True
        else:
            if evaluate_statements_for_permission(allow_statements, permission, resource_arn):
                return True, False
    return False, False


def parse_statement_node_group(node_group):
    return [n._properties for n in node_group]


def get_principals_for_account(neo4j_session, account_id):
    get_policy_query = """
    MATCH
    (acc:AWSAccount{id:{AccountId}})-[:RESOURCE]->
    (principal:AWSPrincipal)-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT principal.arn as principal_arn, policy.id as policy_id, collect(statements) as statements 
    """
    results = neo4j_session.run(
        get_policy_query,
        AccountId=account_id,
    )
    principals = {}
    #{r["principal_arn"}:{r["policy_id"]: parse_statement_node_group(r["statements"])} for r in results}
    for r in results:
        principal_arn = r["principal_arn"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if not principal_arn in principals:
            principals[principal_arn] = {}
        principals[principal_arn][policy_id] = parse_statement_node_group(statements)
    return principals


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


def load_principal_mappings(neo4j_session, principal_mappings, node_type, relationship_name, update_tag):
    map_policy_query = """
    UNWIND {Mapping} as mapping
    MATCH (principal:AWSPrincipal{arn:mapping.principal_arn})
    MATCH (resource:{NodeType}{arn:mapping.resource_arn})
    MERGE (principal)-[r:{RelationshipName}]->(resource)
    SET r.lastupdated = {aws_update_tag}
    """
    #{"principal_arn": principal_arn, "resource_arn": resource_arn}
    if not principal_mappings:
        return
    map_policy_query = map_policy_query.replace("{NodeType}", node_type)
    map_policy_query = map_policy_query.replace("{RelationshipName}", relationship_name)
    neo4j_session.run(
        map_policy_query,
        Mapping=principal_mappings,
        aws_update_tag=update_tag,
    )


def cleanup_rpr(neo4j_session, node_type, relationship_name, update_tag, current_aws_id):
    logger.info("Cleaning up relationship '%s' for node label '%s'", relationship_name, node_type)
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

def evaluate_policies_against_resource(policies, resource_arn, permissions):
    granted = False
    for policy_id, statements in policies.items():
        allowed, explicit_deny = evaluate_policy_for_permission(statements, permissions, resource_arn)
        # If the action is explicitly denied then no other policy can override it
        if explicit_deny:
            return False
        if not granted and allowed:
            granted = True
    
    return granted

def evaluate_relationships(principals, resource_arns, permission):
    allowed_mappings = []
    for resource_arn in resource_arns:
        for principal_arn, policies in principals.items():
            if evaluate_policies_against_resource(policies, resource_arn, permission):
                allowed_mappings.append({"principal_arn": principal_arn, "resource_arn": resource_arn})
    return allowed_mappings

def sync(neo4j_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing Permission Relationships for account '%s'.", account_id)
    principals = get_principals_for_account(neo4j_session, account_id)
    relationship_mapping = parse_permission_relationship_file(common_job_parameters["permission_relationship_file"])
    for rpr in relationship_mapping:
        permissions = rpr["permissions"]
        relationship_name = rpr["relationship_name"]
        target_label = rpr["target_label"]
        resource_arns = get_resource_arns(neo4j_session, account_id, target_label)
        logger.info("Syncing relationship '%s' for node label '%s'", relationship_name, target_label)
        allowed_mappings = evaluate_relationships(principals, resource_arns, permissions)
        load_principal_mappings(neo4j_session, allowed_mappings,
                             target_label, relationship_name, update_tag)
        cleanup_rpr(neo4j_session, target_label, relationship_name, update_tag, account_id)



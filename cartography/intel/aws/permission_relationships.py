import logging
import os
import re
from string import Template

import yaml

from cartography.graph.statement import GraphStatement

logger = logging.getLogger(__name__)


def evaluate_clause(clause, match):
    """ Evaluates the a clause in IAM. Clauses can be AWS [not]actions and [not]resources

    Arguments:
        clause {str, re.Pattern} -- The clause you are evaluating against. Clauses can use
            variable length wildcards (*)
            fixed length wildcards (?)
        match {str} -- The item to match against.

    Returns:
        [bool] -- True if the clause matched, False otherwise
    """
    #

    result = compile_regex(clause).fullmatch(match)
    return result is not None


def evaluate_statement_clause_for_permission(statement, clause_name, match, missing_clause_return=False):
    """ Evaluates a specific clause (action, resource ect) against a match (resource arn or action name)

    Arguments:
        statement {dict} -- The AWS policy statement
        clause_name {str} -- The Clause in the statement to evaluate.
            Can be one of action, notaction, resource, notresource
        match {str, re.Pattern} -- The item to match against

    Keyword Arguments:
        missing_clause_return {bool} -- If the statement doesn't contain the clause_name this is the return type
        (default: {False})

    Returns:
        [type] -- If the specific clause_name grants access to the item
    """
    if clause_name not in statement:
        return missing_clause_return
    for clause in statement[clause_name]:
        if evaluate_clause(clause, match):
            return True
    return False


def evaluate_statements_for_permission(statements, permission, resource_arn):
    """ Evaluate an entire statement for a specific permission against a resource

    Arguments:
        statements {[dict]} -- The list of statements to be evaluated
        permission {str} -- The permission to evaluate
        resource_arn {[type]} -- The resource to test the permission against

    Returns:
        [bool] -- If the statement grants the specific permission to the resource
    """
    allowed = False
    for statement in statements:
        if not evaluate_statement_clause_for_permission(statement, "notaction", permission):
            if evaluate_statement_clause_for_permission(statement, "action", permission, missing_clause_return=True):
                if evaluate_statement_clause_for_permission(statement, "resource", resource_arn):
                    if not evaluate_statement_clause_for_permission(statement, "notresource", resource_arn):
                        return True

    return allowed


def evaluate_policy_for_permission(statements, permissions, resource_arn):
    """ Evaluates an entire policy for specific permissions to a resource.
    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        statements {[dict]} -- The list of statements for the policy
        permissions {[str]} -- The permissions to evaluate
        resource_arn {[type]} -- The resource to test the permission against

    Returns:
        [(bool, bool)] -- (allowed_by_policy, explicitly_denied_by_policy)
        return cases
        (True, False) - The policy allows the action
        (False, False) - The poliy does not allow the action, but also doesn't explicitly deny it
        (False, True) - The policy specifically denies the action. There is no need to evaluate other policies
    """
    allow_statements = [s for s in statements if s["effect"] == "Allow"]
    deny_statements = [s for s in statements if s["effect"] == "Deny"]
    for permission in permissions:
        if evaluate_statements_for_permission(deny_statements, permission, resource_arn):
            # The action explicitly denied then no other policy can override it
            return False, True
        else:
            if evaluate_statements_for_permission(allow_statements, permission, resource_arn):
                # The action is allowed by this policy
                return True, False
    # The action is not allowed by this policy, but not specifically denied either
    return False, False


def evaluate_policies_against_resource(policies, resource_arn, permissions):
    """ Evaluates an enture set of policies for a specific resource for a specific permission

    Arguments:
        policies {[dict]} -- The policys to evaluate
        resource_arn {str} -- The resource to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [bool] -- True if the policies allow the permission against the resource
    """
    granted = False
    for _, statements in policies.items():
        allowed, explicit_deny = evaluate_policy_for_permission(statements, permissions, resource_arn)

        if explicit_deny:

            return False
        if not granted and allowed:
            granted = True

    return granted


def calculate_permission_relationships(principals, resource_arns, permission):
    """ Evaluate principals permissions to resources

    Arguments:
        principals {[dict]} -- The principals to check permission for
        resource_arns {[str]} -- The resources to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [dict] -- The allowed mappings
    """
    allowed_mappings = []
    for resource_arn in resource_arns:
        for principal_arn, policies in principals.items():
            if evaluate_policies_against_resource(policies, resource_arn, permission):
                allowed_mappings.append({"principal_arn": principal_arn, "resource_arn": resource_arn})
    return allowed_mappings


def parse_statement_node(node_group):
    """ Parse a dict from group of Neo4J node

    Arguments:
        node_group {[Neo4j.Node]} -- the node to parse

    Returns:
        [dict] -- A dictionary of statements from the node
    """
    return [n._properties for n in node_group]


def compile_regex(item):
    """ Compile a clause into a regex. Clause checking in AWS is case insensitive

    Arguments:
        item {str} -- the item to create the regex for

    Returns:
        [re.Pattern] -- The precompiled regex pattern.
    """
    if isinstance(item, str):
        item = item.replace(".", "\\.").replace("*", ".*")
        item = re.compile(item, flags=re.IGNORECASE)
    return item


def compile_statement(statements):
    """ Compile a statement by precompiling the regex for the relevant clauses. This is done to boost
    performance by not recompiling the regex over and over again.

    Arguments:
        statements {dict} -- The statement dictionary

    Returns:
        [dict] -- the compiled statement
    """
    properties = ['action', 'resource', 'notresource', 'notaction']
    for statement in statements:
        for statement_property in properties:
            if statement_property in statement:
                statement[statement_property] = [compile_regex(item) for item in statement[statement_property]]
    return statements


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
    for r in results:
        principal_arn = r["principal_arn"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if principal_arn not in principals:
            principals[principal_arn] = {}
        principals[principal_arn][policy_id] = compile_statement(parse_statement_node(statements))
    return principals


def get_resource_arns(neo4j_session, account_id, node_label):
    get_resource_query = Template("""
    MATCH (acc:AWSAccount{id:{AccountId}})-[:RESOURCE]->(resource:$node_label)
    return resource.arn as arn
    """)
    get_resource_query = get_resource_query.safe_substitute(node_label=node_label)
    results = neo4j_session.run(
        get_resource_query,
        AccountId=account_id,
    )
    arns = [r["arn"] for r in results]
    return arns


def load_principal_mappings(neo4j_session, principal_mappings, node_label, relationship_name, update_tag):
    map_policy_query = Template("""
    UNWIND {Mapping} as mapping
    MATCH (principal:AWSPrincipal{arn:mapping.principal_arn})
    MATCH (resource:$node_label{arn:mapping.resource_arn})
    MERGE (principal)-[r:$relationship_name]->(resource)
    SET r.lastupdated = {aws_update_tag}
    """)
    if not principal_mappings:
        return
    map_policy_query = map_policy_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )
    neo4j_session.run(
        map_policy_query,
        Mapping=principal_mappings,
        aws_update_tag=update_tag,
    )


def cleanup_rpr(neo4j_session, node_label, relationship_name, update_tag, current_aws_id):
    logger.info("Cleaning up relationship '%s' for node label '%s'", relationship_name, node_label)
    cleanup_rpr_query = Template("""
        MATCH (:AWSAccount{id: {AWS_ID}})-[:RESOURCE]->(principal:AWSPrincipal)-[r:$relationship_name]->
        (resource:$node_label)
        WHERE r.lastupdated <> {UPDATE_TAG}
        WITH r LIMIT {LIMIT_SIZE}  DELETE (r) return COUNT(*) as TotalCompleted
    """)
    cleanup_rpr_query = cleanup_rpr_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )

    statement = GraphStatement(cleanup_rpr_query, {'UPDATE_TAG': update_tag, 'AWS_ID': current_aws_id}, True, 1000)
    statement.run(neo4j_session)


def parse_permission_relationship_file(file):
    try:
        if not os.path.isabs(file):
            file = os.path.join(os.getcwd(), file)
        with open(file) as f:
            relationship_mapping = yaml.load(f, Loader=yaml.FullLoader)
        return relationship_mapping
    except FileNotFoundError:
        logger.warn(f"Permission relationshp mapping file {file} not found, skipping injestion ")
        return []


def is_valid_rpr(rpr):
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False

    return True


def sync(neo4j_session, account_id, update_tag, common_job_parameters):
    logger.info("Syncing Permission Relationships for account '%s'.", account_id)
    principals = get_principals_for_account(neo4j_session, account_id)
    relationship_mapping = parse_permission_relationship_file(common_job_parameters["permission_relationship_file"])
    for rpr in relationship_mapping:
        if not is_valid_rpr(rpr):
            raise ValueError("""
        Resource permission relationship is missing fields.
        Required fields: permissions, relationship_name, target_label"
        """)
        permissions = rpr["permissions"]
        relationship_name = rpr["relationship_name"]
        target_label = rpr["target_label"]
        resource_arns = get_resource_arns(neo4j_session, account_id, target_label)
        logger.info("Syncing relationship '%s' for node label '%s'", relationship_name, target_label)
        allowed_mappings = calculate_permission_relationships(principals, resource_arns, permissions)
        load_principal_mappings(
            neo4j_session, allowed_mappings,
            target_label, relationship_name, update_tag,
        )
        cleanup_rpr(neo4j_session, target_label, relationship_name, update_tag, account_id)

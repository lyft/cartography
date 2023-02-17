import logging
import os
import re
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Pattern
from typing import Tuple

import boto3
import neo4j
import yaml

from cartography.graph.statement import GraphStatement
from cartography.util import timeit

logger = logging.getLogger(__name__)


def evaluate_clause(clause: str, match: str) -> bool:
    """ Evaluates the a clause in IAM. Clauses can be AWS [not]actions and [not]resources

    Arguments:
        clause {str, re.Pattern} -- The clause you are evaluating against. Clauses can use
            variable length wildcards (*)
            fixed length wildcards (?)
        match {str} -- The item to match against.

    Returns:
        [bool] -- True if the clause matched, False otherwise
    """
    result = compile_regex(clause).fullmatch(match)
    return result is not None


def evaluate_notaction_for_permission(statement: Dict, permission: str) -> bool:
    """Return whether an IAM 'notaction' clause in the given statement applies to the item"""
    if 'notaction' not in statement:
        return False
    for clause in statement['notaction']:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_action_for_permission(statement: Dict, permission: str) -> bool:
    """Return whether an IAM 'action' clause in the given statement applies to the permission"""
    if 'action' not in statement:
        return True
    for clause in statement['action']:
        if evaluate_clause(clause, permission):
            return True
    return False


def evaluate_resource_for_permission(statement: Dict, resource_arn: str) -> bool:
    """Return whether the given IAM 'resource' statement applies to the resource_arn"""
    if 'resource' not in statement:
        return False
    for clause in statement['resource']:
        if evaluate_clause(clause, resource_arn):
            return True
    return False


def evaluate_notresource_for_permission(statement: Dict, resource_arn: str) -> bool:
    """Return whether an IAM 'notresource' clause in the given statement applies to the resource_arn"""
    if 'notresource' not in statement:
        return False
    for clause in statement['notresource']:
        if evaluate_clause(clause, resource_arn):
            return True
    return False


def evaluate_statements_for_permission(statements: List[Dict], permission: str, resource_arn: str) -> bool:
    """ Evaluate an entire statement for a specific permission against a resource

    Arguments:
        statements {[dict]} -- The list of statements to be evaluated
        permission {str} -- The permission to evaluate. ex "s3:GetObject"
        resource_arn {[type]} -- The resource to test the permission against

    Returns:
        [bool] -- If the statement grants the specific permission to the resource
    """

    allowed = False
    for statement in statements:
        if not evaluate_notaction_for_permission(statement, permission):
            if evaluate_action_for_permission(statement, permission):
                if evaluate_resource_for_permission(statement, resource_arn):
                    if not evaluate_notresource_for_permission(statement, resource_arn):
                        return True

    return allowed


def evaluate_policy_for_permissions(
    statements: List[Dict], permissions: List[str], resource_arn: str,
) -> Tuple[bool, bool]:
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


def principal_allowed_on_resource(policies: Dict, resource_arn: str, permissions: List[str]) -> bool:
    """ Evaluates an enture set of policies for a specific resource for a specific permission.


    Arguments:
        policies {[dict]} -- The policys to evaluate
        resource_arn {str} -- The resource to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [bool] -- True if the policies allow the permission against the resource
    """
    if not isinstance(permissions, list):
        raise ValueError("permissions is not a list")
    granted = False
    for _, statements in policies.items():
        allowed, explicit_deny = evaluate_policy_for_permissions(statements, permissions, resource_arn)
        if explicit_deny:
            return False
        if not granted and allowed:
            granted = True

    return granted


def calculate_permission_relationships(
    principals: Dict, resource_arns: List[str], permissions: List[str],
) -> List[Dict]:
    """ Evaluate principals permissions to resources
    This currently only evaluates policies on IAM principals. It does not take into account
    Resource Policies - Policies attached to the resource instead of the IAM principal
    Permission Boundaries - Boundaries for an IAM principal
    Session Policies - Special policies for Federated users

    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        principals {[dict]} -- The principals to check permission for
        resource_arns {[str]} -- The resources to test the permission against
        permissions {[str]} -- The permissions to evaluate

    Returns:
        [dict] -- The allowed mappings
    """
    allowed_mappings: List[Dict] = []
    for resource_arn in resource_arns:
        for principal_arn, policies in principals.items():
            if principal_allowed_on_resource(policies, resource_arn, permissions):
                allowed_mappings.append({"principal_arn": principal_arn, "resource_arn": resource_arn})
    return allowed_mappings


def calculate_seed_admin_principals(
    iam_principals: Dict,
) -> List[Dict]:
    """ calculate_seed_admin_principals
    Arguments:
        iam_principals {[dict]} -- The principals to check permission for

    Returns:
        [dict] -- List of seed principals marked as admin
    """
    seed_admin_principals: List[Dict] = []
    for principal_arn, policies in iam_principals.items():
        if not policies:
            continue

        principal_node_arn_str = ':'.join(principal_arn.split(':')[5:])
        principal_node_type = principal_node_arn_str.split("/")[0]

        # Can principal modify own inline policies to itself.
        if principal_node_type == 'user':
            permission = 'iam:PutUserPolicy'
        elif principal_node_type == 'role':
            permission = 'iam:PutRolePolicy'
        else:
            permission = 'iam:PutGroupPolicy'
        if principal_allowed_on_resource(policies, principal_arn, [permission]):
            seed_admin_principals.append({"principal_arn": principal_arn, "admin_reason": permission})
            continue

        # Can node attach AdministratorAccessPolicy to itself.
        if principal_node_type == 'user':
            permission = 'iam:AttachUserPolicy'
        elif principal_node_type == 'role':
            permission = 'iam:AttachRolePolicy'
        else:
            permission = 'iam:AttachGroupPolicy'
        if principal_allowed_on_resource(policies, principal_arn, [permission]):
            seed_admin_principals.append({"principal_arn": principal_arn, "admin_reason": permission})
            continue

        # TODO: Node can create a role & attach managed policy:
        # AdministratorAccessPolicy or an inline policy.
        # TODO: Can node update attached customer managed policy. (Retrieve policy arn)
        # TODO: Check if node can attach/modify group's policies.
    return seed_admin_principals


def parse_statement_node(node_group: List[Any]) -> List[Any]:
    """ Parse a dict from group of Neo4J node

    Arguments:
        node_group {[Neo4j.Node]} -- the node to parse

    Returns:
        [list] -- A list of statements from the node
    """
    return [n._properties for n in node_group]


def compile_regex(item: str) -> Pattern:
    r""" Compile a clause into a regex. Clause checking in AWS is case insensitive
    The following regex symbols will be replaced to make AWS * and ? matching a regex
    * -> .* (wildcard)
    ? -> .? (single character wildcard)
    . -> \\. (make period a literal period)

    Arguments:
        item {str} -- the item to create the regex for

    Returns:
        [re.Pattern] -- The precompiled regex pattern.
        If the pattern does not compile it will return an re.Pattern of empty string
    """

    if isinstance(item, str):
        item = item.replace(".", "\\.").replace("*", ".*").replace("?", ".?")
        try:
            return re.compile(item, flags=re.IGNORECASE)
        except re.error:
            logger.warning(f"Regex did not compile for {item}")
            # in this case it must still return a regex.
            # So it will return an re.Pattern of empry stringm
            return re.compile("", flags=re.IGNORECASE)
    else:
        return item


def compile_statement(statements: List[Any]) -> List[Any]:
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


def get_principals_for_account(neo4j_session: neo4j.Session, account_id: str) -> Dict:
    get_policy_query = """
    MATCH
    (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
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
    principals: Dict[Any, Any] = {}
    for r in results:
        principal_arn = r["principal_arn"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if principal_arn not in principals:
            principals[principal_arn] = {}
        principals[principal_arn][policy_id] = compile_statement(parse_statement_node(statements))
    return principals


def get_iam_principals_for_account(neo4j_session: neo4j.Session, account_id: str) -> Dict:
    get_iam_principals_query = """
    MATCH
    (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
    (principal:AWSPrincipal)
    WHERE "AWSUser" IN labels(principal) OR
    "AWSGroup" IN labels(principal) OR
    "AWSRole" IN labels(principal)
    OPTIONAL MATCH (principal)-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT principal.arn as principal_arn, policy.id as policy_id, collect(statements) as statements
    """

    results = neo4j_session.run(
        get_iam_principals_query,
        AccountId=account_id,
    )

    iam_principals: Dict[Any, Any] = {}
    for r in results:
        principal_arn = r["principal_arn"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if principal_arn not in iam_principals:
            iam_principals[principal_arn] = {}
        if policy_id is None:
            continue
        iam_principals[principal_arn][policy_id] = compile_statement(parse_statement_node(statements))
    return iam_principals


def get_resource_arns(neo4j_session: neo4j.Session, account_id: str, node_label: str) -> List[Any]:
    get_resource_query = Template("""
    MATCH (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->(resource:$node_label)
    return resource.arn as arn
    """)
    get_resource_query_template = get_resource_query.safe_substitute(node_label=node_label)
    results = neo4j_session.run(
        get_resource_query_template,
        AccountId=account_id,
    )
    arns = [r["arn"] for r in results]
    return arns


def load_principal_mappings(
    neo4j_session: neo4j.Session, principal_mappings: List[Dict], node_label: str,
    relationship_name: str, update_tag: int,
) -> None:
    map_policy_query = Template("""
    UNWIND $Mapping as mapping
    MATCH (principal:AWSPrincipal{arn:mapping.principal_arn})
    MATCH (resource:$node_label{arn:mapping.resource_arn})
    MERGE (principal)-[r:$relationship_name]->(resource)
    SET r.lastupdated = $aws_update_tag
    """)
    if not principal_mappings:
        return
    map_policy_query_template = map_policy_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )
    neo4j_session.run(
        map_policy_query_template,
        Mapping=principal_mappings,
        aws_update_tag=update_tag,
    )


def cleanup_principal_admin_attributes(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
) -> None:
    logger.info("Cleaning up admin attributes")
    admin_cleanup_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (principal:AWSPrincipal)
        SET principal.is_admin = NULL, principal.admin_reason = NULL
    """
    neo4j_session.run(
        admin_cleanup_query,
        AccountId=current_aws_account_id,
    )


def cleanup_rpr(
    neo4j_session: neo4j.Session, node_label: str, relationship_name: str, update_tag: int,
    current_aws_id: str,
) -> None:
    logger.info("Cleaning up relationship '%s' for node label '%s'", relationship_name, node_label)
    cleanup_rpr_query = Template("""
        MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(principal:AWSPrincipal)-[r:$relationship_name]->
        (resource:$node_label)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE  DELETE (r) return COUNT(*) as TotalCompleted
    """)
    cleanup_rpr_query_template = cleanup_rpr_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )

    statement = GraphStatement(
        cleanup_rpr_query_template, {'UPDATE_TAG': update_tag, 'AWS_ID': current_aws_id},
        True, 1000,
    )
    statement.run(neo4j_session)


def parse_permission_relationships_file(file_path: str) -> List[Any]:
    try:
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        with open(file_path) as f:
            relationship_mapping = yaml.load(f, Loader=yaml.FullLoader)
        return relationship_mapping
    except FileNotFoundError:
        logger.warning(
            f"Permission relationships mapping file {file_path} not found, skipping sync stage {__name__}. "
            f"If you want to run this sync, please explicitly set a value for --permission-relationships-file in the "
            f"command line interface.",
        )
        return []


def is_valid_rpr(rpr: Dict) -> bool:
    required_fields = ["permissions", "relationship_name", "target_label"]
    for field in required_fields:
        if field not in rpr:
            return False

    return True


def load_seed_admin_principals(
    neo4j_session: neo4j.Session,
    seed_admin_principals: List[Dict],
) -> None:
    set_seed_admin_query = """
    UNWIND $principals as principal
    MATCH (p:AWSPrincipal{arn:principal.principal_arn})
    SET p.is_admin = True, p.admin_reason = principal.admin_reason
    """
    neo4j_session.run(
        set_seed_admin_query,
        principals=seed_admin_principals,
    )


def set_remaining_admin_principals(neo4j_session: neo4j.Session, current_aws_account_id: str) -> None:
    set_admin_through_role_assumption_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)-[:STS_ASSUMEROLE_ALLOW*..10]->
        (admin:AWSPrincipal)<-[:RESOURCE]-(acc:AWSAccount{id:$AccountId})
        WHERE admin.is_admin = True
        WITH p, COLLECT(admin) as admins
        SET p.is_admin = True,
        p.admin_reason = "Role assumption chain to admin role " +
        admins[0].arn
    """
    neo4j_session.run(
        set_admin_through_role_assumption_query,
        AccountId=current_aws_account_id,
    )

    set_admin_through_group_membership_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)-[:MEMBER_AWS_GROUP]->
        (adminGroup:AWSGroup)<-[:RESOURCE]-(acc:AWSAccount{id:$AccountId})
        WHERE adminGroup.is_admin = True
        WITH p, COLLECT(adminGroup) as adminGroups
        SET p.is_admin = True,
        p.admin_reason = "Member of admin group " + adminGroups[0].arn
    """
    neo4j_session.run(
        set_admin_through_group_membership_query,
        AccountId=current_aws_account_id,
    )


def sync_admin_attributes(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Admin Attributes for account '%s'.", current_aws_account_id)

    cleanup_principal_admin_attributes(neo4j_session, current_aws_account_id)
    iam_principals = get_iam_principals_for_account(neo4j_session, current_aws_account_id)
    seed_admin_principals = calculate_seed_admin_principals(iam_principals)
    load_seed_admin_principals(neo4j_session, seed_admin_principals)
    set_remaining_admin_principals(neo4j_session, current_aws_account_id)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    sync_admin_attributes(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    logger.info("Syncing Permission Relationships for account '%s'.", current_aws_account_id)
    principals = get_principals_for_account(neo4j_session, current_aws_account_id)

    pr_file = common_job_parameters["permission_relationships_file"]
    if not pr_file:
        logger.warning(
            "Permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --permission-relationships-file",
        )
        return
    relationship_mapping = parse_permission_relationships_file(pr_file)
    for rpr in relationship_mapping:
        if not is_valid_rpr(rpr):
            raise ValueError("""
        Resource permission relationship is missing fields.
        Required fields: permissions, relationship_name, target_label"
        """)
        permissions = rpr["permissions"]
        relationship_name = rpr["relationship_name"]
        target_label = rpr["target_label"]
        resource_arns = get_resource_arns(neo4j_session, current_aws_account_id, target_label)
        logger.info("Syncing relationship '%s' for node label '%s'", relationship_name, target_label)
        allowed_mappings = calculate_permission_relationships(principals, resource_arns, permissions)
        load_principal_mappings(
            neo4j_session, allowed_mappings,
            target_label, relationship_name, update_tag,
        )
        cleanup_rpr(neo4j_session, target_label, relationship_name, update_tag, current_aws_account_id)

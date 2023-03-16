import logging
import os
import re
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
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
        bool -- True if the clause matched, False otherwise
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


def evaluate_statements_for_permission(statements: List[Dict], resource_arn: str, permission: str) -> bool:
    """ Evaluate an entire statement for a specific permission against a resource

    Arguments:
        statements {[dict]} -- The list of statements to be evaluated
        permission {str} -- The permission to evaluate. ex "s3:GetObject"
        resource_arn {str} -- The resource to test the permission against

    Returns:
        bool -- If the statement grants the specific permission to the resource
    """

    allowed = False
    for statement in statements:
        if not evaluate_notaction_for_permission(statement, permission):
            if evaluate_action_for_permission(statement, permission):
                if evaluate_resource_for_permission(statement, resource_arn):
                    if not evaluate_notresource_for_permission(statement, resource_arn):
                        return True
    return allowed


def evaluate_policy_for_permission(
    statements: List[Dict], resource_arn: str, permission: str,
) -> Tuple[bool, bool]:
    """ Evaluates an entire policy for specific permission to a resource.
    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        statements {[dict]} -- The list of statements for the policy
        permission {str} -- The permission to evaluate
        resource_arn {str} -- The resource to test the permission against

    Returns:
        [(bool, bool)] -- (allowed_by_policy, explicitly_denied_by_policy)
        return cases
        (True, False) - The policy allows the action
        (False, False) - The poliy does not allow the action, but also doesn't explicitly deny it
        (False, True) - The policy specifically denies the action. There is no need to evaluate other policies
    """
    allow_statements = [s for s in statements if s["effect"] == "Allow"]
    deny_statements = [s for s in statements if s["effect"] == "Deny"]
    if evaluate_statements_for_permission(deny_statements, resource_arn, permission):
        # The action explicitly denied then no other policy can override it
        return False, True
    elif evaluate_statements_for_permission(allow_statements, resource_arn, permission):
        # The action is allowed by this policy
        return True, False
    else:
        # The action is not allowed by this policy, but not specifically denied either
        return False, False


def principal_allowed_on_resource(
    policies: Dict, resource_arn: str, permissions_policy_specs: List[Dict], policy_specs_aggregation: str = "OR",
) -> bool:
    """ Evaluates an entire set of policies for a specific resource for the given policy specs.

    Arguments:
        policies {dict} -- The policys to evaluate
        resource_arn {str} -- The resource to test the permission against
        permissions_policy_specs {[dict]} -- The policy specs to evaluate
        policy_specs_aggregation {str} -- How to aggregate policy specs list

    Returns:
        bool -- True if the policies allow the permission against the resource
    """
    if not isinstance(permissions_policy_specs, list):
        raise ValueError("permissions_policy_specs is not a list")
    if policy_specs_aggregation not in ["AND", "OR"]:
        raise ValueError("policy_specs_aggregation must be AND or OR strings")
    granted: List[bool] = []
    for pps in permissions_policy_specs:
        pps_granted = False
        for _, statements in policies.items():
            if "permission" not in pps:
                raise ValueError("pps dict must have permission field")
            permission = pps["permission"]
            resource_arn = pps["resource"] if "resource" in pps else resource_arn
            allowed, explicit_deny = evaluate_policy_for_permission(statements, resource_arn, permission)
            if explicit_deny:
                pps_granted = False
                break
            if allowed:
                pps_granted = True
        granted.append(pps_granted)
    return any(granted) if policy_specs_aggregation == "OR" else all(granted)


def calculate_permission_relationships(
    principals: Dict,
    resource_arns: List[str],
    permissions_policy_specs: List[Dict],
    resource_spec_matches: Dict,
    policy_specs_aggregation: str,
    principals_admin_status: Dict[str, bool],
    skip_admins: bool,
) -> List[Dict]:
    """ Evaluate principals permissions to resources
    This currently only evaluates policies on IAM principals. It does not take into account
    Resource Policies - Policies attached to the resource instead of the IAM principal
    Permission Boundaries - Boundaries for an IAM principal
    Session Policies - Special policies for Federated users

    AWS Policy evaluation reference
    https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html

    Arguments:
        principals {dict} -- The principals to check permission for
        resource_arns {[str]} -- The resources to test the permission against
        permissions_policy_specs {[Dict]} -- The policy specifications to check for
        resource_spec_matches {Dict} -- Whether resources matches the resource spec
        policy_specs_aggregation {str} -- How to aggregate policy specs

    Returns:
        [dict] -- The allowed mappings
    """
    allowed_mappings: List[Dict] = []
    for resource_arn in resource_arns:
        for principal_arn, policies in principals.items():
            # Skipping self edges
            if principal_arn == resource_arn:
                continue
            # Skipping admins
            if skip_admins and principals_admin_status.get(principal_arn, False):
                continue
            allows: List[bool] = [
                principal_allowed_on_resource(
                    policies,
                    resource_arn,
                    permissions_policy_specs,
                    policy_specs_aggregation,
                ),
            ]
            if resource_spec_matches[resource_arn] is not None:
                allows.append(resource_spec_matches[resource_arn])
            final_allow = any(allows) if policy_specs_aggregation == "OR" else all(allows)
            if final_allow:
                allowed_mappings.append(
                    {"principal_arn": principal_arn, "resource_arn": resource_arn},
                )
    return allowed_mappings


def calculate_seed_high_principals(
    iam_principals: Dict,
) -> List[Dict]:
    """ calculate_seed_high_principals - just adds one reason. This is a very approximate
    calculation of high privileges where notaction and separate statements are not always
    accounted for.
    Arguments:
        iam_principals {[dict]} -- The principals to check permission for

    Returns:
        [dict] -- List of seed principals marked as high
    """
    seed_high_principals: List[Dict] = []
    for principal_arn, policies in iam_principals.items():
        if not policies:
            continue

        # Check for basic administrative access.
        if principal_allowed_on_resource(policies, "*", [{"permission": "*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "AdministratorAccessPolicy"})
            continue

        # Check for high permission for S3 - full access.
        if principal_allowed_on_resource(policies, "*", [{"permission": "s3:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "S3FullAccess"})
            continue
        if principal_allowed_on_resource(policies, "arn:aws:s3:::*", [{"permission": "s3:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "S3FullAccess"})
            continue

        # Check for high permission for RDS - full access.
        if principal_allowed_on_resource(policies, "*", [{"permission": "rds:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "RDSFullAccess"})
            continue
        if principal_allowed_on_resource(policies, "arn:aws:rds:::*", [{"permission": "rds:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "RDSFullAccess"})
            continue

        # Check for high permissions for EC2 - full access
        if principal_allowed_on_resource(policies, "*", [{"permission": "ec2:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "EC2FullAccess"})
            continue
        if principal_allowed_on_resource(policies, "arn:aws:ec2:::*", [{"permission": "ec2:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "EC2FullAccess"})
            continue

        # Check for high permissions for ECR - full access
        if principal_allowed_on_resource(policies, "*", [{"permission": "ecr:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "ECRFullAccess"})
            continue
        if principal_allowed_on_resource(policies, "arn:aws:ecr:::*", [{"permission": "ecr:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "ECRFullAccess"})
            continue

        # Check for high permissions for ECS - full access
        if principal_allowed_on_resource(policies, "*", [{"permission": "ecs:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "ECSFullAccess"})
            continue
        if principal_allowed_on_resource(policies, "arn:aws:ecs:::*", [{"permission": "ecs:*"}]):
            seed_high_principals.append({"principal_arn": principal_arn, "high_reason": "ECSFullAccess"})
            continue
    return seed_high_principals


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

        if principal_allowed_on_resource(policies, "*", [{"permission": "*"}]):
            seed_admin_principals.append({"principal_arn": principal_arn, "admin_reason": "AdministratorAccessPolicy"})
            continue

        # Can principal modify own inline policies to itself.
        if principal_node_type == 'user':
            permission = 'iam:PutUserPolicy'
        elif principal_node_type == 'role':
            permission = 'iam:PutRolePolicy'
        else:
            permission = 'iam:PutGroupPolicy'
        if principal_allowed_on_resource(policies, principal_arn, [{"permission": permission}]):
            seed_admin_principals.append({"principal_arn": principal_arn, "admin_reason": permission})
            continue

        # Can node attach AdministratorAccessPolicy to itself.
        if principal_node_type == 'user':
            permission = 'iam:AttachUserPolicy'
        elif principal_node_type == 'role':
            permission = 'iam:AttachRolePolicy'
        else:
            permission = 'iam:AttachGroupPolicy'
        if principal_allowed_on_resource(policies, principal_arn, [{"permission": permission}]):
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


def get_principals_for_account(neo4j_session: neo4j.Session, account_id: str) -> Tuple[Dict, Dict]:
    get_policy_query = """
    MATCH
    (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
    (principal:AWSPrincipal)-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT principal.arn as principal_arn, principal.is_admin as is_admin, policy.id as policy_id,
    collect(statements) as statements
    """
    results = neo4j_session.run(
        get_policy_query,
        AccountId=account_id,
    )
    principals: Dict[Any, Any] = {}
    principals_admin_status: Dict[Any, bool] = {}
    for r in results:
        principal_arn = r["principal_arn"]
        is_admin = r["is_admin"]
        policy_id = r["policy_id"]
        statements = r["statements"]
        if principal_arn not in principals:
            principals[principal_arn] = {}
        principals[principal_arn][policy_id] = compile_statement(parse_statement_node(statements))
        principals_admin_status[principal_arn] = (is_admin is True)
    return principals, principals_admin_status


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


def get_resource_spec_matches(
    neo4j_session: neo4j.Session, resource_policy_specs: List[Dict], resource_arns: List[str],
) -> Dict:
    """
    For each resource_arn, return whether it meets the resource policy spec.
    Currently, we assume resource_policy_specs is a list of size <= 1 with a service key.
    """
    resource_arn_to_match: Dict = {
        resource_arn: None for resource_arn in resource_arns
    }
    if len(resource_policy_specs) == 0:
        return resource_arn_to_match

    service_to_match = resource_policy_specs[0]["service"]
    get_resource_service_query = """
    UNWIND $resource_arns as resource_arn
    OPTIONAL MATCH (resource:AWSRole{arn:resource_arn})-[:TRUSTS_AWS_PRINCIPAL]->
    (p:AWSPrincipal)
    WHERE p.type = 'Service'
    AND p.arn = $service_to_match
    return resource_arn, COUNT(p) > 0 as match
    """
    results = neo4j_session.run(
        get_resource_service_query,
        resource_arns=resource_arns,
        service_to_match=service_to_match,
    )

    for res in results:
        resource_arn, match = res["resource_arn"], res["match"]
        resource_arn_to_match[resource_arn] = match
    return resource_arn_to_match


def load_principal_mappings(
    neo4j_session: neo4j.Session, principal_mappings: List[Dict], node_label: str,
    relationship_name: str, relationship_reason: Optional[str], update_tag: int,
) -> None:
    map_policy_query = Template("""
    UNWIND $Mapping as mapping
    MATCH (principal:AWSPrincipal{arn:mapping.principal_arn})
    MATCH (resource:$node_label{arn:mapping.resource_arn})
    MERGE (principal)-[r:$relationship_name]->(resource)
    SET r.lastupdated = $aws_update_tag,
    r.relationship_reason = $relationship_reason
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
        relationship_reason=relationship_reason,
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


def cleanup_principal_high_attributes(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
) -> None:
    logger.info("Cleaning up high attributes")
    admin_cleanup_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (principal:AWSPrincipal)
        SET principal.is_high = NULL, principal.high_reason = NULL
    """
    neo4j_session.run(
        admin_cleanup_query,
        AccountId=current_aws_account_id,
    )


def cleanup_rpr(
    neo4j_session: neo4j.Session,
    node_label: str,
    relationship_name: str,
    relationship_reason: Optional[str],
    update_tag: int,
    current_aws_id: str,
) -> None:
    logger.info("Cleaning up relationship '%s' for node label '%s'", relationship_name, node_label)
    cleanup_rpr_query = Template("""
        MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(principal:AWSPrincipal)-[r:$relationship_name]->
        (resource:$node_label)
        WHERE r.lastupdated <> $UPDATE_TAG
        AND r.relationship_reason = $relationship_reason
        WITH r LIMIT $LIMIT_SIZE  DELETE (r) return COUNT(*) as TotalCompleted
    """)
    cleanup_rpr_query_template = cleanup_rpr_query.safe_substitute(
        node_label=node_label,
        relationship_name=relationship_name,
    )

    statement = GraphStatement(
        cleanup_rpr_query_template,
        {
            'UPDATE_TAG': update_tag,
            'AWS_ID': current_aws_id,
            'relationship_reason': relationship_reason,
        },
        True,
        1000,
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


def is_valid_spec(rpr: Dict) -> bool:
    required_fields = [
        "target_label",
        "permissions_policy_specs",
        "policy_specs_aggregation",
        "relationship_name",
        "skip_admins",
    ]
    for field in required_fields:
        if field not in rpr:
            return False
    if not isinstance(rpr["target_label"], str):
        return False
    if not isinstance(rpr["permissions_policy_specs"], list):
        return False
    for pps in rpr["permissions_policy_specs"]:
        pps_keys = pps.keys()
        if "permission" not in pps_keys:
            return False
        if len(pps_keys) > 2:
            return False
        if len(pps_keys) == 2 and "resource" not in pps_keys:
            return False
    if "resource_policy_specs" in rpr:
        if not isinstance(rpr["resource_policy_specs"], list):
            return False
        if len(rpr["resource_policy_specs"]) != 1:
            return False
        if "service" not in rpr["resource_policy_specs"][0]:
            return False
        if rpr["target_label"] != "AWSRole":
            return False
    if rpr["policy_specs_aggregation"] not in ["AND", "OR"]:
        return False
    if not isinstance(rpr["relationship_name"], str):
        return False
    if "relationship_reason" in rpr and not isinstance(rpr["relationship_reason"], str):
        return False
    if not isinstance(rpr["skip_admins"], bool):
        return False
    return True


def load_seed_high_principals(
    neo4j_session: neo4j.Session,
    seed_high_principals: List[Dict],
) -> None:
    set_seed_admin_query = """
    UNWIND $principals as principal
    MATCH (p:AWSPrincipal{arn:principal.principal_arn})
    SET p.is_seed_high = True, p.is_high = True, p.high_reason = principal.high_reason
    """
    neo4j_session.run(
        set_seed_admin_query,
        principals=seed_high_principals,
    )


def set_remaining_high_principals(neo4j_session: neo4j.Session, current_aws_account_id: str) -> None:
    set_high_through_role_assumption_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)-[:STS_ASSUMEROLE_ALLOW*..10]->
        (high:AWSPrincipal)<-[:RESOURCE]-(acc:AWSAccount{id:$AccountId})
        WHERE high.is_high = True
        WITH p, COLLECT(high) as highPrincipals
        SET p.is_high = True,
        p.high_reason = "Role assumption chain to high privilege role " +
        highPrincipals[0].arn
    """
    neo4j_session.run(
        set_high_through_role_assumption_query,
        AccountId=current_aws_account_id,
    )

    set_high_through_group_membership_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)-[:MEMBER_AWS_GROUP]->
        (highGroup:AWSGroup)<-[:RESOURCE]-(acc:AWSAccount{id:$AccountId})
        WHERE highGroup.is_high = True
        WITH p, COLLECT(highGroup) as highGroups
        SET p.is_high = True,
        p.high_reason = "Member of high privilege group " + highGroups[0].arn
    """
    neo4j_session.run(
        set_high_through_group_membership_query,
        AccountId=current_aws_account_id,
    )

    # Set high to true if admin is true.
    set_high_through_admin_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)
        WHERE p.is_admin = True
        SET p.is_high = True,
        p.high_reason = p.admin_reason
    """
    neo4j_session.run(
        set_high_through_admin_query,
        AccountId=current_aws_account_id,
    )


def load_seed_admin_principals(
    neo4j_session: neo4j.Session,
    seed_admin_principals: List[Dict],
) -> None:
    set_seed_admin_query = """
    UNWIND $principals as principal
    MATCH (p:AWSPrincipal{arn:principal.principal_arn})
    SET p.is_seed_admin = True, p.is_admin = True, p.admin_reason = principal.admin_reason
    """
    neo4j_session.run(
        set_seed_admin_query,
        principals=seed_admin_principals,
    )


def set_remaining_admin_principals(neo4j_session: neo4j.Session, current_aws_account_id: str) -> None:
    set_admin_through_role_assumption_query = """
        MATCH
        (acc:AWSAccount{id:$AccountId})-[:RESOURCE]->
        (p:AWSPrincipal)-[:STS_ASSUME_ROLE_ALLOW*..10]->
        (admin:AWSPrincipal)<-[:RESOURCE]-(acc)
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
        (adminGroup:AWSGroup)<-[:RESOURCE]-(acc)
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
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    iam_principals: Dict,
) -> None:
    logger.info("Syncing Admin Attributes for account '%s'.", current_aws_account_id)

    cleanup_principal_admin_attributes(neo4j_session, current_aws_account_id)
    seed_admin_principals = calculate_seed_admin_principals(iam_principals)
    load_seed_admin_principals(neo4j_session, seed_admin_principals)
    set_remaining_admin_principals(neo4j_session, current_aws_account_id)


def sync_high_attributes(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    iam_principals: Dict,
) -> None:
    logger.info("Syncing High Attributes for account '%s'.", current_aws_account_id)

    cleanup_principal_high_attributes(neo4j_session, current_aws_account_id)
    seed_high_principals = calculate_seed_high_principals(iam_principals)
    load_seed_high_principals(neo4j_session, seed_high_principals)
    set_remaining_high_principals(neo4j_session, current_aws_account_id)


def sync_permission_relationships(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Permission Relationships for account '%s'.", current_aws_account_id)
    principals, principals_admin_status = get_principals_for_account(
        neo4j_session, current_aws_account_id,
    )

    pr_file = common_job_parameters["permission_relationships_file"]
    if not pr_file:
        logger.warning(
            "Permission relationships file was not specified, skipping. If this is not expected, please check your "
            "value of --permission-relationships-file",
        )
        return
    relationship_mapping = parse_permission_relationships_file(pr_file)
    for rel_mapping in relationship_mapping:
        if not is_valid_spec(rel_mapping):
            raise ValueError(
                f'Invalid rel_mapping spec {rel_mapping}',
            )
        target_label = rel_mapping["target_label"]
        permissions_policy_specs = rel_mapping["permissions_policy_specs"]
        resource_policy_specs = rel_mapping.get("resource_policy_specs", [])
        policy_specs_aggregation = rel_mapping["policy_specs_aggregation"]
        relationship_name = rel_mapping["relationship_name"]
        relationship_reason = rel_mapping.get("relationship_reason", None)
        skip_admins = rel_mapping["skip_admins"]
        resource_arns = get_resource_arns(neo4j_session, current_aws_account_id, target_label)
        resource_spec_matches = get_resource_spec_matches(
            neo4j_session, resource_policy_specs, resource_arns,
        )
        logger.info(
            "Syncing relationship '%s' with reason '%s' for node label '%s'",
            relationship_name,
            relationship_reason,
            target_label,
        )
        allowed_mappings = calculate_permission_relationships(
            principals,
            resource_arns,
            permissions_policy_specs,
            resource_spec_matches,
            policy_specs_aggregation,
            principals_admin_status,
            skip_admins,
        )
        load_principal_mappings(
            neo4j_session,
            allowed_mappings,
            target_label,
            relationship_name,
            relationship_reason,
            update_tag,
        )
        cleanup_rpr(
            neo4j_session,
            target_label,
            relationship_name,
            relationship_reason,
            update_tag,
            current_aws_account_id,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    iam_principals = get_iam_principals_for_account(neo4j_session, current_aws_account_id)

    sync_admin_attributes(
        neo4j_session,
        current_aws_account_id,
        iam_principals,
    )

    sync_high_attributes(
        neo4j_session,
        current_aws_account_id,
        iam_principals,
    )

    sync_permission_relationships(
        neo4j_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

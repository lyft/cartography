import json
import logging
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import OtherRelationships
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.aws.iam_future.util import create_policy_id
from cartography.intel.aws.iam_future.util import create_policy_statement_id
from cartography.intel.aws.iam_future.util import ensure_list
from cartography.intel.aws.iam_future.util import PolicyType
from cartography.util import timeit


logger = logging.getLogger(__name__)

# AWS Policy


@dataclass(frozen=True)
class AWSPolicyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('current_aws_account_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSPolicyToAWSAccountRelProperties = AWSPolicyToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('PolicyId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('Name')
    type: PropertyRef = PropertyRef('PolicyType')


@dataclass(frozen=True)
class AWSPolicyToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyToAWSPrincipal(CartographyRelSchema):
    target_node_label: str = 'AWSPrincipal'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'arn': PropertyRef('PrincipalArn')})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: AWSPolicyToAWSPrincipalRelProperties = AWSPolicyToAWSPrincipalRelProperties()


@dataclass(frozen=True)
class AWSPolicySchema(CartographyNodeSchema):
    label: str = "AWSPolicy"
    properties: AWSPolicyNodeProperties = AWSPolicyNodeProperties()
    sub_resource_relationship: AWSPolicyToAWSAccount = AWSPolicyToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships([
        AWSPolicyToAWSPrincipal(),
    ])


# AWS Policy Statements
@dataclass(frozen=True)
class AWSPolicyStatementToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyStatementToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('current_aws_account_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSPolicyStatementToAWSAccountRelProperties = AWSPolicyStatementToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSPolicyStatementNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    effect: PropertyRef = PropertyRef('Effect')
    action: PropertyRef = PropertyRef('Action')
    notaction: PropertyRef = PropertyRef("NotAction")
    resource: PropertyRef = PropertyRef("Resource")
    notresource: PropertyRef = PropertyRef("NotResource")
    condition: PropertyRef = PropertyRef("Condition")
    sid: PropertyRef = PropertyRef("Sid")


@dataclass(frozen=True)
class AWSPolicyStatementToAWSPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyStatementToAWSPolicy(CartographyRelSchema):
    target_node_label: str = 'AWSPolicy'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({'id': PropertyRef('PolicyId')})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "STATEMENT"
    properties: AWSPolicyStatementToAWSPolicyRelProperties = AWSPolicyStatementToAWSPolicyRelProperties()


@dataclass(frozen=True)
class AWSPolicyStatementSchema(CartographyNodeSchema):
    label: str = "AWSPolicyStatement"
    properties: AWSPolicyStatementNodeProperties = AWSPolicyStatementNodeProperties()
    sub_resource_relationship: AWSPolicyStatementToAWSAccount = AWSPolicyStatementToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships([
        AWSPolicyStatementToAWSPolicy(),
    ])


@timeit
def get_user_policy_data(
        boto3_session: boto3.session.Session,
        user_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Retrieve user policy data for each user in user_list.
    :return: Datashape = {
        <user ARN>: {
            <policy_name (str)>: <policy_statement (Dict)>,
            ...
        },
        ...
    }
    """
    resource_client = boto3_session.resource('iam')
    user_policy_map = {}
    for user in user_list:
        name = user["UserName"]
        arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            user_policy_map[arn] = {p.name: p.policy_document["Statement"] for p in resource_user.policies.all()}
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
            )
    return user_policy_map


def transform_user_policies(user_policy_map: Dict[str, Any], policy_type: str) -> List[Dict[str, str]]:
    result = []
    for principal_arn, p_contents in user_policy_map.items():
        for policy_name, _ in p_contents.items():
            result.append(
                {
                    'PolicyId': create_policy_id(principal_arn, policy_type, policy_name),
                    'Name': policy_name,
                    'PolicyType': policy_type,
                    'PrincipalArn': principal_arn,
                },
            )
    return result


def transform_user_policy_statements(user_policy_map: Dict[str, Any], policy_type: str) -> List[Dict[str, str]]:
    count = 1
    result = []

    for principal_arn, p_contents in user_policy_map.items():
        for policy_name, statements in p_contents.items():
            policy_id = create_policy_id(principal_arn, policy_type, policy_name)
            if not isinstance(statements, list):
                statements = [statements]

            for stmt in statements:
                if 'Sid' not in stmt:
                    statement_sid = str(count)
                    count += 1
                else:
                    statement_sid = stmt['Sid']
                result.append(
                    {
                        'Sid': statement_sid,
                        'Id': create_policy_statement_id(policy_id, statement_sid),
                        'Effect': stmt['Effect'],
                        'Action': ensure_list(stmt['Action']) if 'Action' in stmt else None,
                        'NotAction': ensure_list(stmt['NotAction']) if 'NotAction' in stmt else None,
                        'Resource': ensure_list(stmt['Resource']) if 'Resource' in stmt else None,
                        'NotResource': ensure_list(stmt['NotResource']) if 'NotResource' in stmt else None,
                        'Condition': json.dumps(ensure_list(stmt["Condition"])),
                    },
                )
    return result


def load_user_policies(
        neo4j_session: neo4j.Session,
        dict_list: List[Dict[str, str]],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingestion_query = build_ingestion_query(
        AWSPolicySchema(),
        selected_relationships={AWSPolicyStatementToAWSPolicy()},  # TODO - remove when allowing connection to sub res
    )
    load_graph_data(
        neo4j_session,
        ingestion_query,
        dict_list,
        lastupdated=aws_update_tag,
        current_aws_account_id=current_aws_account_id,
    )


def load_user_policy_statements(
        neo4j_session: neo4j.Session,
        dict_list: List[Dict[str, str]],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingestion_query = build_ingestion_query(
        AWSPolicyStatementSchema(),
        selected_relationships={AWSPolicyToAWSPrincipal()},  # TODO - remove when allowing connection to sub resource
    )
    load_graph_data(
        neo4j_session,
        ingestion_query,
        dict_list,
        lastupdated=aws_update_tag,
        current_aws_account_id=current_aws_account_id,
    )


@timeit
def sync_user_policies(
        boto3_session: boto3.session.Session,
        user_data: Dict[str, Any],
        neo4j_session: neo4j.Session,
        aws_update_tag: int,
        current_aws_account_id: str,
) -> None:
    policy_data = get_user_policy_data(boto3_session, user_data['Users'])
    transformed_policy_data = transform_user_policies(policy_data, PolicyType.inline.value)
    load_user_policies(neo4j_session, transformed_policy_data, current_aws_account_id, aws_update_tag)

    transformed_statement_data = transform_user_policy_statements(policy_data, PolicyType.inline.value)
    load_user_policy_statements(neo4j_session, transformed_statement_data, current_aws_account_id, aws_update_tag)

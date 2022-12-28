import logging
from dataclasses import dataclass
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyRelProperties, PropertyRef, CartographyRelSchema, TargetNodeMatcher, \
    make_target_node_matcher, LinkDirection, CartographyNodeProperties, CartographyNodeSchema, OtherRelationships
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.aws.iam_future.util import create_policy_id, PolicyType
from cartography.util import timeit


logger = logging.getLogger(__name__)


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


@timeit
def get_user_inline_policy_data(boto3_session: boto3.session.Session, user_list: list[dict]) -> dict:
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


def transform_user_inline_policies(user_policy_map: dict[str, Any], policy_type: str) -> list[dict[str, str]]:
    result = []
    for principal_arn, p_contents in user_policy_map.items():
        for policy_name, _ in p_contents.items():
            result.append(
                {
                    'PolicyId': create_policy_id(principal_arn, policy_type, policy_name),
                    'Name': policy_name,
                    'PolicyType': policy_type,
                    'PrincipalArn': principal_arn,
                }
            )
    return result


def load_user_inline_policies(
        neo4j_session: neo4j.Session,
        dict_list: list[dict[str, str]],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingestion_query = build_ingestion_query(
        AWSPolicySchema(),
        selected_relationships={AWSPolicyToAWSPrincipal()},
    )
    load_graph_data(
        neo4j_session,
        ingestion_query,
        dict_list,
        lastupdated=aws_update_tag,
        current_aws_account_id=current_aws_account_id,
    )


@timeit
def sync_user_inline_policies(
        boto3_session: boto3.session.Session,
        user_data: dict,
        neo4j_session: neo4j.Session,
        aws_update_tag: int,
        current_aws_account_id: str,
) -> None:
    policy_data = get_user_inline_policy_data(boto3_session, user_data['Users'])
    policy_data = transform_user_inline_policies(policy_data, PolicyType.inline.value)
    load_user_inline_policies(neo4j_session, policy_data, current_aws_account_id, aws_update_tag)

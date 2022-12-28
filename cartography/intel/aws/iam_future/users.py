import logging
from dataclasses import dataclass
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.graph.model import CartographyRelProperties, PropertyRef, CartographyRelSchema, TargetNodeMatcher, \
    make_target_node_matcher, LinkDirection, CartographyNodeProperties, CartographyNodeSchema, ExtraNodeLabels
from cartography.graph.querybuilder import build_ingestion_query
from cartography.util import timeit

logger = logging.getLogger(__name__)



@dataclass(frozen=True)
class AWSUserToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('current_aws_account_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSUserToAWSAccountRelProperties = AWSUserToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSUserNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('Arn')
    id: PropertyRef = PropertyRef('Arn')
    userid: PropertyRef = PropertyRef('UserId')
    createdate: PropertyRef = PropertyRef('CreateDate'),
    name: PropertyRef = PropertyRef('UserName')
    path: PropertyRef = PropertyRef('Path')
    passwordlastused: PropertyRef = PropertyRef('PasswordLastUsed')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)



@dataclass(frozen=True)
class AWSUserToRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AWSUserToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('current_aws_account_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSUserToAWSAccountRelProperties = AWSUserToAWSAccountRelProperties()



@dataclass(frozen=True)
class AWSUserSchema(CartographyNodeSchema):
    label: str = "AWSUser"
    properties: AWSUserNodeProperties = AWSUserNodeProperties()
    sub_resource_relationship: AWSUserToAWSAccount = AWSUserToAWSAccount()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(['AWSPrincipal'])


@timeit
def get_user_list_data(boto3_session: boto3.session.Session) -> dict:
    client = boto3_session.client('iam')

    paginator = client.get_paginator('list_users')
    users: list[dict[str, Any]] = []
    for page in paginator.paginate():
        users.extend(page['Users'])
    return {'Users': users}


def transform_user_list_data(data: dict[str, Any]):
    for user in data['Users']:
        if 'CreateDate' in user:
            user['CreateDate'] = str(user['CreateDate'])
    return data


@timeit
def load_users(
    neo4j_session: neo4j.Session, users: dict[str, Any], current_aws_account_id: str, aws_update_tag: int,
) -> None:
    ingestion_query = build_ingestion_query(AWSUserSchema())
    load_graph_data(
        neo4j_session,
        ingestion_query,
        users['Users'],
        lastupdated=aws_update_tag,
        current_aws_account_id=current_aws_account_id,
    )


@timeit
def sync_iam_users(
        boto3_session: boto3.Session,
        neo4j_session: neo4j.Session,
        aws_update_tag: int,
        current_aws_account_id: str,
) -> dict[str, Any]:
    logger.info("Syncing IAM users for account '%s'.", current_aws_account_id)
    user_data = get_user_list_data(boto3_session)
    user_data = transform_user_list_data(user_data)
    load_users(neo4j_session, user_data['Users'], current_aws_account_id, aws_update_tag)
    return user_data

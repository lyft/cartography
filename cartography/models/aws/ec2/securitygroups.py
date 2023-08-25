from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2SecurityGroupNodeProperties(CartographyNodeProperties):
    # arn: PropertyRef = PropertyRef('Arn', extra_index=True) # TODO decide on this
    id: PropertyRef = PropertyRef('GroupId')
    groupid: PropertyRef = PropertyRef('GroupId', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SecurityGroupToAwsAccountRelProperties = EC2SecurityGroupToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2SubnetToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: EC2SubnetToEC2InstanceRelProperties = EC2SubnetToEC2InstanceRelProperties()


@dataclass(frozen=True)
class EC2SecurityGroupSchema(CartographyNodeSchema):
    label: str = 'EC2SecurityGroup'
    properties: EC2SecurityGroupNodeProperties = EC2SecurityGroupNodeProperties()
    sub_resource_relationship: EC2SecurityGroupToAWSAccount = EC2SecurityGroupToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SecurityGroupToEC2Instance(),
        ],
    )

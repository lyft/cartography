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
class EC2NetworkInterfaceNodeProperties(CartographyNodeProperties):
    # arn: PropertyRef = PropertyRef('Arn', extra_index=True) TODO decide this
    id: PropertyRef = PropertyRef('NetworkInterfaceId')
    status: PropertyRef = PropertyRef('Status')
    mac_address: PropertyRef = PropertyRef('MacAddress')
    description: PropertyRef = PropertyRef('Description')
    private_dns_name: PropertyRef = PropertyRef('PrivateDnsName')
    private_ip_address: PropertyRef = PropertyRef('PrivateIpAddress')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2NetworkInterfaceToAwsAccountRelProperties = EC2NetworkInterfaceToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToEC2InstanceRelProperties = EC2NetworkInterfaceToEC2InstanceRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2Subnet(CartographyRelSchema):
    target_node_label: str = 'EC2Subnet'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('SubnetId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2NetworkInterfaceToEC2SubnetRelProperties = EC2NetworkInterfaceToEC2SubnetRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SecurityGroup(CartographyRelSchema):
    target_node_label: str = 'EC2SecurityGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('GroupId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: EC2NetworkInterfaceToEC2SubnetRelProperties = EC2NetworkInterfaceToEC2SubnetRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceSchema(CartographyNodeSchema):
    label: str = 'NetworkInterface'
    properties: EC2NetworkInterfaceNodeProperties = EC2NetworkInterfaceNodeProperties()
    sub_resource_relationship: EC2NetworkInterfaceToAWSAccount = EC2NetworkInterfaceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkInterfaceToEC2Instance(),
            EC2NetworkInterfaceToEC2Subnet(),
            EC2NetworkInterfaceToEC2SecurityGroup(),
        ],
    )

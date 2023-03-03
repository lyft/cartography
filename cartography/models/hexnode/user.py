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
class HexnodeUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    tenant: PropertyRef = PropertyRef('tenant', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    email: PropertyRef = PropertyRef('email')
    phone: PropertyRef = PropertyRef('phone')
    domain: PropertyRef = PropertyRef('domain')


@dataclass(frozen=True)
class HexnodeUserToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HexnodeDevice)<-[:OWNS_DEVICE]-(:HexnodeUser)
class HexnodeUserToDeviceRel(CartographyRelSchema):
    target_node_label: str = 'HexnodeDevice'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'user_id': PropertyRef('id')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNS_DEVICE"
    properties: HexnodeUserToDeviceRelProperties = HexnodeUserToDeviceRelProperties()


@dataclass(frozen=True)
class HumanToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HexnodeUser)<-[:IDENTITY_HEXNODE]-(:Human)
class HumanToUserRel(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_HEXNODE"
    properties: HumanToUserRelProperties = HumanToUserRelProperties()


@dataclass(frozen=True)
class HexnodeUserSchema(CartographyNodeSchema):
    label: str = 'HexnodeUser'
    properties: HexnodeUserNodeProperties = HexnodeUserNodeProperties()
    sub_resource_relationship: HexnodeUserToDeviceRel = HexnodeUserToDeviceRel()
    other_relationships: OtherRelationships = OtherRelationships(rels=[HumanToUserRel()])

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
class HexnodeDeviceGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    tenant: PropertyRef = PropertyRef('tenant', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('groupname')
    description: PropertyRef = PropertyRef('description')
    group_type: PropertyRef = PropertyRef('grouptype')
    modified_date: PropertyRef = PropertyRef('modified_date')


@dataclass(frozen=True)
class DeviceGroupToPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HexnodeDeviceGroup)-[:APPLIES_POLICY]->(:HexnodePolicy)
class DeviceGroupToPolicyRel(CartographyRelSchema):
    target_node_label: str = 'HexnodePolicy'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('policy_id')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_POLICY"
    properties: DeviceGroupToPolicyRelProperties = DeviceGroupToPolicyRelProperties()


@dataclass(frozen=True)
class DeviceGroupToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HexnodeDeviceGroup)<-[:MEMBER_OF]-(:HexnodePolicy)
class DeviceGroupToDeviceRel(CartographyRelSchema):
    target_node_label: str = 'HexnodeDevice'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('device_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: DeviceGroupToDeviceRelProperties = DeviceGroupToDeviceRelProperties()


@dataclass(frozen=True)
class HexnodeDeviceGroupSchema(CartographyNodeSchema):
    label: str = 'HexnodeDeviceGroup'
    properties: HexnodeDeviceGroupNodeProperties = HexnodeDeviceGroupNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[DeviceGroupToPolicyRel(), DeviceGroupToDeviceRel()],
    )

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class HexnodeTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class HexnodeTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HexnodeTenant)<-[:RESOURCE]-(:HexnodeUser)
class HexnodeTenantToUserRel(CartographyRelSchema):
    target_node_label: str = 'HexnodeUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'tenant_id': PropertyRef('id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HexnodeTenantToUserRelProperties = HexnodeTenantToUserRelProperties()


@dataclass(frozen=True)
class HexnodeTenantSchema(CartographyNodeSchema):
    label: str = 'HexnodeTenant'
    properties: HexnodeTenantNodeProperties = HexnodeTenantNodeProperties()
    sub_resource_relationship: HexnodeTenantToUserRel = HexnodeTenantToUserRel()

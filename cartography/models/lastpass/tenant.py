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
class LastpassTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class TenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:LastpassTenant)<-[:RESOURCE]-(:LastpassUser)
class LastpassTenantToUserRel(CartographyRelSchema):
    target_node_label: str = 'LastpassUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('tenant_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenantToUserRelProperties = TenantToUserRelProperties()


@dataclass(frozen=True)
class LastpassTenantSchema(CartographyNodeSchema):
    label: str = 'LastpassTenant'
    properties: LastpassTenantNodeProperties = LastpassTenantNodeProperties()
    sub_resource_relationship: LastpassTenantToUserRel = LastpassTenantToUserRel()

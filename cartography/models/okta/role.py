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
class OktaRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    type: PropertyRef = PropertyRef("type")
    permission: PropertyRef = PropertyRef("permission")
    conditions: PropertyRef = PropertyRef("conditions")
    isEditable: PropertyRef = PropertyRef("isEditable")
    cursor: PropertyRef = PropertyRef("cursor")


@dataclass(frozen=True)
class OktaRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)<-[:RESOURCE]-(:OktaOrganization)
class OktaRoleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaRoleToOktaOrganizationRelProperties = (
        OktaRoleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaRoleToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
# (:OktaRole)<-[:ASSIGNED_TO_ROLE]-(:OktaUser)
class OktaRoleToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: OktaRoleToOktaUserRelProperties = (
        OktaRoleToOktaUserRelProperties()
    )



@dataclass(frozen=True)
class OktaRoleSchema(CartographyNodeSchema):
    label: str = "OktaRole"
    properties: OktaRoleNodeProperties = OktaRoleNodeProperties()
    sub_resource_relationship: OktaRoleToOktaOrganizationRel = (
        OktaRoleToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaRoleToOktaUserRel()
        ],
    )

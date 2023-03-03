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
class CleverCloudAddonProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    real_id: PropertyRef = PropertyRef('realId')
    region: PropertyRef = PropertyRef('region')
    provider_id: PropertyRef = PropertyRef('provider.id')
    provider_name: PropertyRef = PropertyRef('provider.name')
    plan_id: PropertyRef = PropertyRef('plan.id')
    plan_slug: PropertyRef = PropertyRef('plan.slug')
    plan_name: PropertyRef = PropertyRef('plan.name')
    creation_date: PropertyRef = PropertyRef('creationDate')


@dataclass(frozen=True)
class AddonToOrganizationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CleverCloudAddon)-[:RESOURCE]->(:CleverCloudOrganization)
class AddonToOrganization(CartographyRelSchema):
    target_node_label: str = 'CleverCloudOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('org_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AddonToOrganizationProperties = AddonToOrganizationProperties()


@dataclass(frozen=True)
class CleverCloudAddonSchema(CartographyNodeSchema):
    label: str = 'CleverCloudAddon'
    properties: CleverCloudAddonProperties = CleverCloudAddonProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[AddonToOrganization(), AddonToOrganization()],
    )

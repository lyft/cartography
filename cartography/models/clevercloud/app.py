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
class CleverCloudApplicationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    description: PropertyRef = PropertyRef('description')
    zone: PropertyRef = PropertyRef('zone')
    instance_type: PropertyRef = PropertyRef('instance.type')
    instance_version: PropertyRef = PropertyRef('instance.version')
    instance_slug: PropertyRef = PropertyRef('instance.variant.slug')
    instance_name: PropertyRef = PropertyRef('instance.variant.name')
    deployment_shutdownable: PropertyRef = PropertyRef('deployment.shutdownable')
    deployment_type: PropertyRef = PropertyRef('deployment.type')
    creation_date: PropertyRef = PropertyRef('creationDate')
    archived: PropertyRef = PropertyRef('archived')
    separate_build: PropertyRef = PropertyRef('separate_build')
    state: PropertyRef = PropertyRef('state')
    git_commit: PropertyRef = PropertyRef('commitId')
    git_branch: PropertyRef = PropertyRef('branch')
    force_https: PropertyRef = PropertyRef('forceHttps')


@dataclass(frozen=True)
class ApplicationToOrganizationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CleverCloudApplication)-[:RESOURCE]->(:CleverCloudOrganization)
class ApplicationToOrganization(CartographyRelSchema):
    target_node_label: str = 'CleverCloudOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('org_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ApplicationToOrganizationProperties = ApplicationToOrganizationProperties()


@dataclass(frozen=True)
class ApplicationToAddonProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CleverCloudApplication)<-[:RESOURCE]-(:CleverCloudAddon)
class ApplicationToAddon(CartographyRelSchema):
    target_node_label: str = 'CleverCloudAddon'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('addon_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ApplicationToAddonProperties = ApplicationToAddonProperties()


@dataclass(frozen=True)
class CleverCloudApplicationSchema(CartographyNodeSchema):
    label: str = 'CleverCloudApplication'
    properties: CleverCloudApplicationProperties = CleverCloudApplicationProperties()
    sub_resource_relationship: ApplicationToAddon = ApplicationToAddon()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[ApplicationToOrganization(), ApplicationToOrganization()],
    )

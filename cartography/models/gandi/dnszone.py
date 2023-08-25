from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GandiDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('fqdn', extra_index=True)
    tld: PropertyRef = PropertyRef('tld')
    organization_id: PropertyRef = PropertyRef('sharing_space.id')
    # Dates
    created_at: PropertyRef = PropertyRef('dates.created_at')
    deletes_at: PropertyRef = PropertyRef('dates.deletes_at')
    hold_begins_at: PropertyRef = PropertyRef('dates.hold_begins_at')
    hold_ends_at: PropertyRef = PropertyRef('dates.hold_ends_at')
    pending_delete_ends_at: PropertyRef = PropertyRef('dates.pending_delete_ends_at')
    registry_created_at: PropertyRef = PropertyRef('dates.registry_created_at')
    registry_ends_at: PropertyRef = PropertyRef('dates.registry_ends_at')
    renew_begins_at: PropertyRef = PropertyRef('dates.renew_begins_at')
    restore_ends_at: PropertyRef = PropertyRef('dates.restore_ends_at')
    updated_at: PropertyRef = PropertyRef('dates.updated_at')
    authinfo_expires_at: PropertyRef = PropertyRef('dates.authinfo_expires_at')
    # Informations
    status: PropertyRef = PropertyRef('status')
    services: PropertyRef = PropertyRef('services')
    # Autorenew
    autorenew_duration: PropertyRef = PropertyRef('autorenew.duration')
    autorenew_enabled: PropertyRef = PropertyRef('autorenew.enabled')


@dataclass(frozen=True)
class OrganizationToDNSZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:GandiOrganization)-[:RESOURCE]->(:GandiDNSZone)
class OrganizationToDNSZoneRel(CartographyRelSchema):
    target_node_label: str = 'GandiOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('sharing_space.id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OrganizationToDNSZoneRelProperties = OrganizationToDNSZoneRelProperties()


@dataclass(frozen=True)
class GandiDNSZoneSchema(CartographyNodeSchema):
    label: str = 'GandiDNSZone'
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(['DNSZone'])
    properties: GandiDNSZoneNodeProperties = GandiDNSZoneNodeProperties()
    sub_resource_relationship: OrganizationToDNSZoneRel = OrganizationToDNSZoneRel()

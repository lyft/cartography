from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GandiDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('fqdn', extra_index=True)
    tld: PropertyRef = PropertyRef('tld')
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
class GandiDNSZoneSchema(CartographyNodeSchema):
    label: str = 'GandiDNSZone'
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(['DNSZone'])
    properties: GandiDNSZoneNodeProperties = GandiDNSZoneNodeProperties()
    # TODO: Link to organization: sub_resource_relationship: XXXRel = XXXRel()
    # Use sharing_space.id or sharing_space.name to link to organization

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class HexnodePolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    tenant: PropertyRef = PropertyRef('tenant', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    description: PropertyRef = PropertyRef('description')
    version: PropertyRef = PropertyRef('version')
    archived: PropertyRef = PropertyRef('archived')
    ios_configured: PropertyRef = PropertyRef('ios_configured')
    android_configured: PropertyRef = PropertyRef('android_configured')
    windows_configured: PropertyRef = PropertyRef('windows_configured')
    created_time: PropertyRef = PropertyRef('created_time')
    modified_time: PropertyRef = PropertyRef('modified_time')


@dataclass(frozen=True)
class HexnodePolicySchema(CartographyNodeSchema):
    label: str = 'HexnodePolicy'
    properties: HexnodePolicyNodeProperties = HexnodePolicyNodeProperties()

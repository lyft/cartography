from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class IPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    ip: PropertyRef = PropertyRef('ip', extra_index=True)


@dataclass(frozen=True)
class IPSchema(CartographyNodeSchema):
    label: str = 'Ip'
    properties: IPNodeProperties = IPNodeProperties()

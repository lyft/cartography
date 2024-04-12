from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class KandjiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated')
    device_id: PropertyRef = PropertyRef('device_id')
    device_name: PropertyRef = PropertyRef('device_name')
    last_check_in: PropertyRef = PropertyRef('last_check_in')
    model: PropertyRef = PropertyRef('model')
    os_version: PropertyRef = PropertyRef('os_version')
    platform: PropertyRef = PropertyRef('platform')
    serial_number: PropertyRef = PropertyRef('serial_number')


@dataclass(frozen=True)
class KandjiDeviceSchema(CartographyNodeSchema):
    label: str = 'KandjiDevice'  # The label of the node
    properties: KandjiDeviceNodeProperties = KandjiDeviceNodeProperties()  # An object representing all properties

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class KandjiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated')
    serial_number: PropertyRef = PropertyRef('serial_number')
    device_name: PropertyRef = PropertyRef('device_name')
    model: PropertyRef = PropertyRef('device.model')
    platform: PropertyRef = PropertyRef('platform')
    os_version: PropertyRef = PropertyRef('os_version')
    last_check_in: PropertyRef = PropertyRef('last_check_in')


@dataclass(frozen=True)
class KandjiDeviceSchema(CartographyNodeSchema):
    label: str = 'KandjiDevice'  # The label of the node
    properties: KandjiDeviceNodeProperties = KandjiDeviceNodeProperties()  # An object representing all properties

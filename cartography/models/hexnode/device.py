from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class HexnodeDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    tenant: PropertyRef = PropertyRef('tenant', set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef('user.id')
    name: PropertyRef = PropertyRef('device_name')
    model_name: PropertyRef = PropertyRef('model_name')
    os_name: PropertyRef = PropertyRef('os_name')
    os_version: PropertyRef = PropertyRef('os_version')
    enrolled_time: PropertyRef = PropertyRef('enrolled_time')
    last_reported: PropertyRef = PropertyRef('last_reported')
    compliant: PropertyRef = PropertyRef('compliant')
    serial_number: PropertyRef = PropertyRef('serial_number')
    enrollment_status: PropertyRef = PropertyRef('enrollment_status')
    imei: PropertyRef = PropertyRef('imei')


@dataclass(frozen=True)
class HexnodeDeviceSchema(CartographyNodeSchema):
    label: str = 'HexnodeDevice'
    properties: HexnodeDeviceNodeProperties = HexnodeDeviceNodeProperties()

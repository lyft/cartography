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
class KandjiDeviceSchema(CartographyNodeSchema):
    label: str = 'KandjiDevice'  # The label of the node
    properties: KandjiDeviceNodeProperties = KandjiDeviceNodeProperties()  # An object representing all properties


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

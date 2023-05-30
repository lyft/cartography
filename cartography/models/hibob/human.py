from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class HumanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('email')
    email: PropertyRef = PropertyRef('email')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('displayName')
    family_name: PropertyRef = PropertyRef('surname')
    given_name: PropertyRef = PropertyRef('firstName')
    gender: PropertyRef = PropertyRef('home.localGender')


@dataclass(frozen=True)
class HumanSchema(CartographyNodeSchema):
    label: str = 'Human'
    properties: HumanNodeProperties = HumanNodeProperties()

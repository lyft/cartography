from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SemgrepDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    slug: PropertyRef = PropertyRef('slug')


@dataclass(frozen=True)
class SemgrepDeploymentSchema(CartographyNodeSchema):
    label: str = 'SemgrepDeployment'
    properties: SemgrepDeploymentProperties = SemgrepDeploymentProperties()

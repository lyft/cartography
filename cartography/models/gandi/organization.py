from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GandiOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    orgname: PropertyRef = PropertyRef('orgname')
    firstname: PropertyRef = PropertyRef('firstname')
    lastname: PropertyRef = PropertyRef('lastname')
    type: PropertyRef = PropertyRef('type')
    email: PropertyRef = PropertyRef('email')
    reseller: PropertyRef = PropertyRef('reseller')
    corporate: PropertyRef = PropertyRef('corporate')
    siren: PropertyRef = PropertyRef('siren')
    vat_number: PropertyRef = PropertyRef('vat_number')


@dataclass(frozen=True)
class GandiOrganizationSchema(CartographyNodeSchema):
    label: str = 'GandiOrganization'
    properties: GandiOrganizationNodeProperties = GandiOrganizationNodeProperties()

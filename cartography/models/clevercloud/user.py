from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties


@dataclass(frozen=True)
class CleverCloudUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('member.id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    organization_id: PropertyRef = PropertyRef('org_id', set_in_kwargs=True)
    email: PropertyRef = PropertyRef('member.email')
    name: PropertyRef = PropertyRef('member.name')
    avatar: PropertyRef = PropertyRef('member.avatar')
    preferred_mfa: PropertyRef = PropertyRef('member.preferredMFA')
    role: PropertyRef = PropertyRef('role')
    job: PropertyRef = PropertyRef('job')

@dataclass(frozen=True)
class CleverCloudUserToClerverCloudOrganizationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class CleverCloudUserSchema(CartographyNodeSchema):
    label: str = 'CleverCloudUser'
    properties: CleverCloudUserProperties = CleverCloudUserProperties()

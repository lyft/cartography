from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


# Organization
@dataclass(frozen=True)
class CleverCloudOrganizationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    description: PropertyRef = PropertyRef('description')
    billing_email: PropertyRef = PropertyRef('billingEmail')
    address: PropertyRef = PropertyRef('address')
    city: PropertyRef = PropertyRef('city')
    zipcode: PropertyRef = PropertyRef('zipcode')
    country: PropertyRef = PropertyRef('country')
    company: PropertyRef = PropertyRef('company')
    vat: PropertyRef = PropertyRef('VAT')
    avatar: PropertyRef = PropertyRef('avatar')
    vat_state: PropertyRef = PropertyRef('vatState')
    customer_fullname: PropertyRef = PropertyRef('customerFullName')
    can_pay: PropertyRef = PropertyRef('canPay')
    clever_enterprise: PropertyRef = PropertyRef('cleverEnterprise')
    emergency_number: PropertyRef = PropertyRef('emergencyNumber')
    can_sepa: PropertyRef = PropertyRef('canSEPA')
    is_trusted: PropertyRef = PropertyRef('isTrusted')


@dataclass(frozen=True)
class OrganizationToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CleverCloudUser)-[:MEMBER_OF]->(:CleverCloudOrganization)
class OrganizationToUserRel(CartographyRelSchema):
    target_node_label: str = 'CleverCloudUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'organization_id': PropertyRef('id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: OrganizationToUserRelProperties = OrganizationToUserRelProperties()


@dataclass(frozen=True)
class CleverCloudOrganizationSchema(CartographyNodeSchema):
    label: str = 'CleverCloudOrganization'
    properties: CleverCloudOrganizationProperties = CleverCloudOrganizationProperties()
    sub_resource_relationship: OrganizationToUserRel = OrganizationToUserRel()

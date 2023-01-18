from dataclasses import dataclass

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.model import OtherRelationships


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
class CleverCloudOrganizationSchema(CartographyNodeSchema):
    label: str = 'CleverCloudOrganization'
    properties: CleverCloudOrganizationProperties = CleverCloudOrganizationProperties()

# User
@dataclass(frozen=True)
class CleverCloudUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('member.id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
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
# (:CleverCloudUser)-[:MEMBER_OF]->(:CleverCloudOrganization)
class CleverCloudUserToCleverCloudOrganization(CartographyRelSchema):
    target_node_label: str = 'CleverCloudOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('orgId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: CleverCloudUserToClerverCloudOrganizationProperties = CleverCloudUserToClerverCloudOrganizationProperties()

@dataclass(frozen=True)
class CleverCloudUserSchema(CartographyNodeSchema):
    label: str = 'CleverCloudUser'
    properties: CleverCloudUserProperties = CleverCloudUserProperties()
    sub_resource_relationship: CleverCloudUserToCleverCloudOrganization = CleverCloudUserToCleverCloudOrganization()

# Application
@dataclass(frozen=True)
class CleverCloudApplicationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    description: PropertyRef = PropertyRef('description')
    zone: PropertyRef = PropertyRef('zone')
    instance_type: PropertyRef = PropertyRef('instance.type')
    instance_version: PropertyRef = PropertyRef('instance.version')
    instance_slug: PropertyRef = PropertyRef('instance.variant.slug')
    instance_name: PropertyRef = PropertyRef('instance.variant.name')
    deployment_shutdownable: PropertyRef = PropertyRef('deployment.shutdownable')
    deployment_type: PropertyRef = PropertyRef('deployment.type')
    creation_date: PropertyRef = PropertyRef('creationDate')
    archived: PropertyRef = PropertyRef('archived')
    separate_build: PropertyRef = PropertyRef('separate_build')
    state: PropertyRef = PropertyRef('state')
    git_commit: PropertyRef = PropertyRef('commitId')
    git_branch: PropertyRef = PropertyRef('branch')
    force_https: PropertyRef = PropertyRef('forceHttps')

@dataclass(frozen=True)
class CleverCloudAppToClerverCloudOrganizationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

@dataclass(frozen=True)
# (:CleverCloudApplication)<-[:RESOURCE]-(:CleverCloudOrganization)
class CleverCloudApplicationToCleverCloudOrganization(CartographyRelSchema):
    target_node_label: str = 'CleverCloudOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ownerId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CleverCloudAppToClerverCloudOrganizationProperties = CleverCloudAppToClerverCloudOrganizationProperties()

@dataclass(frozen=True)
class CleverCloudApplicationSchema(CartographyNodeSchema):
    label: str = 'CleverCloudApplication'
    properties: CleverCloudApplicationProperties = CleverCloudApplicationProperties()
    sub_resource_relationship: CleverCloudApplicationToCleverCloudOrganization = CleverCloudApplicationToCleverCloudOrganization()

# Addons
@dataclass(frozen=True)
class CleverCloudAddonProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    real_id: PropertyRef = PropertyRef('realId')
    region: PropertyRef = PropertyRef('region')
    provider_id: PropertyRef = PropertyRef('provider.id')
    provider_name: PropertyRef = PropertyRef('provider.name')
    plan_id: PropertyRef = PropertyRef('plan.id')
    plan_slug: PropertyRef = PropertyRef('plan.slug')
    plan_name: PropertyRef = PropertyRef('plan.name')
    creation_date: PropertyRef = PropertyRef('creationDate')

@dataclass(frozen=True)
class CleverCloudAddonToClerverCloudOrganizationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

@dataclass(frozen=True)
# (:CleverCloudAddon)<-[:RESOURCE]-(:CleverCloudOrganization)
class CleverCloudAddonToCleverCloudOrganization(CartographyRelSchema):
    target_node_label: str = 'CleverCloudOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('orgId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CleverCloudAppToClerverCloudOrganizationProperties = CleverCloudAppToClerverCloudOrganizationProperties()

# WIP: Application relations ?

@dataclass(frozen=True)
class CleverCloudAddonSchema(CartographyNodeSchema):
    label: str = 'CleverCloudAddon'
    properties: CleverCloudAddonProperties = CleverCloudAddonProperties()
    sub_resource_relationship: CleverCloudAddonToCleverCloudOrganization = CleverCloudAddonToCleverCloudOrganization()
    # WIP: Rel ?

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
class HumanToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CleverCloudUser)<-[:IDENTITY_CLEVERCLOUD]-(:Human)
class HumanToUserRel(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_CLEVERCLOUD"
    properties: HumanToUserRelProperties = HumanToUserRelProperties()


@dataclass(frozen=True)
class CleverCloudUserSchema(CartographyNodeSchema):
    label: str = 'CleverCloudUser'
    properties: CleverCloudUserProperties = CleverCloudUserProperties()
    other_relationships: OtherRelationships = OtherRelationships(rels=[HumanToUserRel()])

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
class DuoUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('user_id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    alias1: PropertyRef = PropertyRef('alias1')
    alias2: PropertyRef = PropertyRef('alias2')
    alias3: PropertyRef = PropertyRef('alias3')
    alias4: PropertyRef = PropertyRef('alias4')
    aliases: PropertyRef = PropertyRef('aliases')
    created: PropertyRef = PropertyRef('created')
    desktoptokens: PropertyRef = PropertyRef('desktoptokens')
    email: PropertyRef = PropertyRef('email', extra_index=True)
    firstname: PropertyRef = PropertyRef('firstname')
    is_enrolled: PropertyRef = PropertyRef('is_enrolled')
    last_directory_sync: PropertyRef = PropertyRef('last_directory_sync')
    last_login: PropertyRef = PropertyRef('last_login')
    lastname: PropertyRef = PropertyRef('lastname')
    notes: PropertyRef = PropertyRef('notes')
    realname: PropertyRef = PropertyRef('realname')
    status: PropertyRef = PropertyRef('status')
    tokens: PropertyRef = PropertyRef('tokens')
    u2ftokens: PropertyRef = PropertyRef('u2ftokens')
    user_id: PropertyRef = PropertyRef('user_id', extra_index=True)
    username: PropertyRef = PropertyRef('username', extra_index=True)
    webauthncredentials: PropertyRef = PropertyRef('webauthncredentials')


@dataclass(frozen=True)
class DuoUserToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoUserToDuoApiHostRel(CartographyRelSchema):
    target_node_label: str = 'DuoApiHost'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DUO_API_HOSTNAME', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoUserToDuoApiHostRelProperties = DuoUserToDuoApiHostRelProperties()


class DuoPhoneToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoPhoneToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoPhone'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PHONE_DUO"
    properties: DuoPhoneToDuoUserRelProperties = DuoPhoneToDuoUserRelProperties()


class DuoEndpointToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoEndpoint'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENDPOINT_DUO"
    properties: DuoEndpointToDuoUserRelProperties = DuoEndpointToDuoUserRelProperties()


class DuoGroupToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoGroupToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'group_id': PropertyRef('group_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_DUO_GROUP"
    properties: DuoGroupToDuoUserRelProperties = DuoGroupToDuoUserRelProperties()


@dataclass(frozen=True)
class DuoUserToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:DuoUser)<-[:IDENTITY_DUO]-(:Human)
class DuoUserToHumanRel(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_DUO"
    properties: DuoUserToHumanRelProperties = DuoUserToHumanRelProperties()


@dataclass(frozen=True)
class DuoUserSchema(CartographyNodeSchema):
    label: str = 'DuoUser'
    properties: DuoUserNodeProperties = DuoUserNodeProperties()
    sub_resource_relationship: DuoUserToDuoApiHostRel = DuoUserToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoUserToHumanRel(),
            DuoEndpointToDuoUserRel(),
            DuoGroupToDuoUserRel(),
        ],
    )

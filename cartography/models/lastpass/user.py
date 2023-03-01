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
class LastpassUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    tenant_id: PropertyRef = PropertyRef('tenant_id', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('fullname')
    email: PropertyRef = PropertyRef('username')
    created: PropertyRef = PropertyRef('created')
    last_pw_change: PropertyRef = PropertyRef('last_pw_change')
    last_login: PropertyRef = PropertyRef('last_login')
    neverloggedin: PropertyRef = PropertyRef('neverloggedin')
    disabled: PropertyRef = PropertyRef('disabled')
    admin: PropertyRef = PropertyRef('admin')
    totalscore: PropertyRef = PropertyRef('totalscore')
    mpstrength: PropertyRef = PropertyRef('mpstrength')
    sites: PropertyRef = PropertyRef('sites')
    notes: PropertyRef = PropertyRef('notes')
    formfills: PropertyRef = PropertyRef('formfills')
    applications: PropertyRef = PropertyRef('applications')
    attachments: PropertyRef = PropertyRef('attachments')
    password_reset_required: PropertyRef = PropertyRef('password_reset_required')
    multifactor: PropertyRef = PropertyRef('multifactor')


@dataclass(frozen=True)
class HumanToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:LastpassUser)<-[:IDENTITY_LASTPASS]-(:Human)
class HumanToUserRel(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_LASTPASS"
    properties: HumanToUserRelProperties = HumanToUserRelProperties()


@dataclass(frozen=True)
class LastpassUserSchema(CartographyNodeSchema):
    label: str = 'LastpassUser'
    properties: LastpassUserNodeProperties = LastpassUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(rels=[HumanToUserRel()])

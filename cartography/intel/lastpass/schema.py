from dataclasses import dataclass

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import PropertyRef


@dataclass(frozen=True)
class LastpassUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
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
class LastpassUserSchema(CartographyNodeSchema):
    label: str = 'LastpassUser'
    properties: LastpassUserNodeProperties = LastpassUserNodeProperties()

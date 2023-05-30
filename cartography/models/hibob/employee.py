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
class HiBobEmployeeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('displayName')
    title: PropertyRef = PropertyRef('work.title')
    family_name: PropertyRef = PropertyRef('surname')
    given_name: PropertyRef = PropertyRef('firstName')
    gender: PropertyRef = PropertyRef('home.localGender')
    email: PropertyRef = PropertyRef('email')
    private_mobile: PropertyRef = PropertyRef('home.mobilePhone')
    private_phone: PropertyRef = PropertyRef('home.privatePhone')
    private_email: PropertyRef = PropertyRef('home.privateEmail')
    start_date: PropertyRef = PropertyRef('work.startDate')
    is_manager: PropertyRef = PropertyRef('work.isManager')
    work_phone: PropertyRef = PropertyRef('work.workPhone')
    work_office: PropertyRef = PropertyRef('work.site')
    department: PropertyRef = PropertyRef('work.department')
    company_id: PropertyRef = PropertyRef('companyId')


@dataclass(frozen=True)
class HiBobEmployeeToHiBobEmployeeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class HiBobEmployeeToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HiBobEmployee)-[:MANAGED_BY]->(:HiBobEmployee)
class HiBobEmployeeToHiBobEmployee(CartographyRelSchema):
    target_node_label: str = 'HiBobEmployee'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'name': PropertyRef('work.reportsTo')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MANAGED_BY"
    properties: HiBobEmployeeToHiBobEmployeeRelProperties = HiBobEmployeeToHiBobEmployeeRelProperties()


@dataclass(frozen=True)
# (:HiBobEmployee)<-[:IS_EMPLOYEE]-(:Human)
class HiBobEmployeeToHuman(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IS_EMPLOYEE"
    properties: HiBobEmployeeToHumanRelProperties = HiBobEmployeeToHumanRelProperties()


@dataclass(frozen=True)
class HiBobEmployeeSchema(CartographyNodeSchema):
    label: str = 'HiBobEmployee'
    properties: HiBobEmployeeNodeProperties = HiBobEmployeeNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        HiBobEmployeeToHuman(),
        HiBobEmployeeToHiBobEmployee(),
    ])

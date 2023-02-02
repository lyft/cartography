from dataclasses import dataclass

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import OtherRelationships
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher


@dataclass(frozen=True)
class HiBobDepartmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')


@dataclass(frozen=True)
class HiBobDepartmentSchema(CartographyNodeSchema):
    label: str = 'HiBobDepartment'
    properties: HiBobDepartmentNodeProperties = HiBobDepartmentNodeProperties()


@dataclass(frozen=True)
class HumanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('email')
    email: PropertyRef = PropertyRef('email')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('displayName')
    family_name: PropertyRef = PropertyRef('surname')
    given_name: PropertyRef = PropertyRef('firstName')
    gender: PropertyRef = PropertyRef('home.localGender')


@dataclass(frozen=True)
class HumanSchema(CartographyNodeSchema):
    label: str = 'Human'
    properties: HumanNodeProperties = HumanNodeProperties()


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


@dataclass(frozen=True)
class HiBobEmployeeToHiBobEmployeeRelProperties(CartographyRelProperties):
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
class HiBobEmployeeToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


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
class HiBobEmployeeToDepartmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HiBobEmployee)-[:MEMBER_OF]->(:HiBobDepartment)
class HiBobEmployeeToHiBobDepartment(CartographyRelSchema):
    target_node_label: str = 'HiBobDepartment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('work.department')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: HiBobEmployeeToDepartmentRelProperties = HiBobEmployeeToDepartmentRelProperties()


@dataclass(frozen=True)
class HiBobEmployeeSchema(CartographyNodeSchema):
    label: str = 'HiBobEmployee'
    properties: HiBobEmployeeNodeProperties = HiBobEmployeeNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        HiBobEmployeeToHuman(),
        HiBobEmployeeToHiBobEmployee(),
        HiBobEmployeeToHiBobDepartment(),
    ])

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class HiBobDepartmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    company_id: PropertyRef = PropertyRef('company_id')


@dataclass(frozen=True)
class HiBobDepartmentToEmployeeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HiBobDepartment)<-[:MEMBER_OF]-(:HiBobEmployee)
class HiBobDepartmentToEmployeeRel(CartographyRelSchema):
    target_node_label: str = 'HiBobEmployee'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'department': PropertyRef('id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: HiBobDepartmentToEmployeeRelProperties = HiBobDepartmentToEmployeeRelProperties()


@dataclass(frozen=True)
class HiBobDepartmentSchema(CartographyNodeSchema):
    label: str = 'HiBobDepartment'
    properties: HiBobDepartmentNodeProperties = HiBobDepartmentNodeProperties()
    sub_resource_relationship: HiBobDepartmentToEmployeeRel = HiBobDepartmentToEmployeeRel()

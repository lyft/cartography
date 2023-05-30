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
class HiBobCompanyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class HiBobCompanyToDepartmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:HiBobCompany)<-[:RESOURCE]-(:HiBobDepartment)
class HiBobCompanyToDepartmentRel(CartographyRelSchema):
    target_node_label: str = 'HiBobDepartment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'company_id': PropertyRef('id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HiBobCompanyToDepartmentRelProperties = HiBobCompanyToDepartmentRelProperties()


@dataclass(frozen=True)
class HiBobCompanySchema(CartographyNodeSchema):
    label: str = 'HiBobCompany'
    properties: HiBobCompanyNodeProperties = HiBobCompanyNodeProperties()
    sub_resource_relationship: HiBobCompanyToDepartmentRel = HiBobCompanyToDepartmentRel()

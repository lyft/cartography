from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import default_field


@dataclass
class TestComputerToPersonRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass
class TestComputerToPersonRel(CartographyRelSchema):
    """
    (:TestComputer)<-[:OWNS]-(:Person)
    """
    target_node_label: str = 'Person'
    target_node_key_refs: Dict[str, PropertyRef] = default_field(
        {
            'first_name': PropertyRef('FirstName'),
            'last_name': PropertyRef('LastName'),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TestComputerToPersonRelProps = TestComputerToPersonRelProps()


# Test defining a simple node with no relationships.
@dataclass
class TestComputerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    ram_gb: PropertyRef = PropertyRef('RAM_GB')
    num_cores: PropertyRef = PropertyRef('NumCores')
    name: PropertyRef = PropertyRef('name')


@dataclass
class TestComputer(CartographyNodeSchema):
    label: str = 'TestComputer'
    properties: TestComputerProperties = TestComputerProperties()
    other_relationships: Optional[List[CartographyRelSchema]] = default_field([TestComputerToPersonRel()])

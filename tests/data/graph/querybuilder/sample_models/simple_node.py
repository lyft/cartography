from dataclasses import dataclass
from typing import Dict

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import default_field


# Test defining a simple node with no relationships.
@dataclass
class SimpleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    property1: PropertyRef = PropertyRef('property1')
    property2: PropertyRef = PropertyRef('property2')


@dataclass
class SimpleNodeSchema(CartographyNodeSchema):
    label: str = 'SimpleNode'
    properties: SimpleNodeProperties = SimpleNodeProperties()


# Test defining a simple node with a sub resource rel: (:SimpleNode)<-[:RESOURCE]-(:SubResource)
@dataclass
class SimpleNodeToSubResourceRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass
class SimpleNodeToSubResourceRel(CartographyRelSchema):
    target_node_label: str = 'SubResource'
    target_node_key_refs: Dict[str, PropertyRef] = default_field(
        {'id': PropertyRef('sub_resource_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RELATIONSHIP_LABEL"
    properties: SimpleNodeToSubResourceRelProps = SimpleNodeToSubResourceRelProps()


@dataclass
class SimpleNodeWithSubResourceSchema(CartographyNodeSchema):
    label: str = 'SimpleNode'
    properties: SimpleNodeProperties = SimpleNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SimpleNodeToSubResourceRel()

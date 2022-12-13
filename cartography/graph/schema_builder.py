from dataclasses import make_dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import default_field


def build_data_class(name: str, base: Type, **props: Any):
    '''
    Helper to build any dataclass. class Returns an instance if the class.
    '''
    cls = make_dataclass(
        cls_name=name,
        bases=(base,),
        fields=[
            (prop_name, type(prop_value), prop_value)
            for prop_name, prop_value in props.items()
        ],
    )
    return cls()


def build_rel_properties(name: str, **properties: PropertyRef):
    '''
    Helper to build a CartographyRelProperties class.
    '''
    return build_data_class(name, CartographyRelProperties, **properties)


def build_rel_schema(
    name: str,
    target_node_label: str,
    target_node_key_refs: Dict[str, PropertyRef],
    direction: LinkDirection,
    rel_label: str,
    properties: CartographyRelProperties,
):
    '''
    Helper to build a CartographyRelSchema class.
    '''
    return build_data_class(
        name,
        CartographyRelSchema,
        target_node_label=target_node_label,
        target_node_key_refs=default_field(target_node_key_refs),
        direction=direction,
        rel_label=rel_label,
        properties=properties,
    )


def build_node_properties(name: str, **properties: PropertyRef):
    '''
    Helper to build a CartographyNodeProperties.
    '''
    return build_data_class(name, CartographyNodeProperties, **properties)


def build_node_schema(
    name: str,
    label: str,
    properties: CartographyNodeProperties,
    sub_resource_relationship: Optional[CartographyRelSchema] = None,
    other_relationships: Optional[List[CartographyRelSchema]] = None,
    extra_labels: Optional[List[str]] = None,
) -> CartographyNodeSchema:
    '''
    Helper function to create a CartographyNodeSchema subclass,
     without explicitly defining a the new class.
    '''
    return build_data_class(
        name,
        CartographyNodeSchema,
        label=label,
        properties=properties,
        sub_resource_relationship=sub_resource_relationship,
        other_relationships=other_relationships,
        extra_labels=extra_labels,
    )

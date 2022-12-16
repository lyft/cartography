from dataclasses import make_dataclass
from typing import Any
from typing import List
from typing import Optional
from typing import Type

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher


def build_data_class(cls_name: str, base_cls: Type, **props: Any):
    '''
    Helper to build any dataclass. class Returns an instance if the class.
    '''
    cls = make_dataclass(
        cls_name=cls_name,
        bases=(base_cls,),
        fields=[
            (prop_name, type(prop_value), prop_value)
            for prop_name, prop_value in props.items()
        ],
        frozen=True,
    )
    return cls()


def build_rel_properties(cls_name: str, **properties: PropertyRef):
    '''
    Helper to build a CartographyRelProperties class.
    '''
    return build_data_class(cls_name, CartographyRelProperties, **properties)


def build_rel_schema(
    cls_name: str,
    target_node_label: str,
    target_node_matcher: TargetNodeMatcher,
    direction: LinkDirection,
    rel_label: str,
    properties: CartographyRelProperties,
):
    '''
    Helper to build a CartographyRelSchema class.
    '''
    return build_data_class(
        cls_name,
        CartographyRelSchema,
        target_node_label=target_node_label,
        target_node_matcher=target_node_matcher,
        direction=direction,
        rel_label=rel_label,
        properties=properties,
    )


def build_node_properties(cls_name: str, **properties: PropertyRef):
    '''
    Helper to build a CartographyNodeProperties.
    '''
    return build_data_class(cls_name, CartographyNodeProperties, **properties)


def build_node_schema(
    cls_name: str,
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
        cls_name,
        CartographyNodeSchema,
        label=label,
        properties=properties,
        sub_resource_relationship=sub_resource_relationship,
        other_relationships=other_relationships,
        extra_labels=extra_labels,
    )

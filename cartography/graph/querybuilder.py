from string import Template
from typing import Dict, Optional
from typing import List
from enum import Enum
from enum import auto


class LinkDirection(Enum):
    OUTWARD = auto()
    INWARD = auto()


class PropertyRef:
    def __init__(self, name: str, static=False):
        self.name = name
        self.static = static

    def _parameterize_name(self) -> str:
        # TODO in neo4j 4.x, we will want to change this to `${self.name}` instead
        # of "{" + self.name "}"
        return "{" + self.name + "}"

    def __repr__(self) -> str:
        return f"item.{self.name}" if not self.static else self._parameterize_name()


class CartographyLink:
    def __init__(
            self,
            label: str,
            key: str,
            dict_field_ref: PropertyRef,
            rel_label: str,
            direction: LinkDirection = None,
            rel_property_map: Dict[str, PropertyRef] = None,
    ):
        self.label = label
        self.key = key
        self.dict_field_ref = dict_field_ref
        self.rel_label = rel_label
        self.direction = LinkDirection.INWARD if not direction else direction
        self.rel_property_map = rel_property_map


def _build_node_properties_statement(
        node_property_map: Dict[str, PropertyRef],
        node_extra_labels: List[str],
) -> Optional[str]:
    ingest_fields_template = Template('            i.$node_property = $property_ref')
    set_clause = 'i.lastupdated = {UpdateTag}'

    # If the node_property_map contains more than just `id`, generate a SET statement for the other fields.
    if len(node_property_map.keys()) > 1:
        set_clause += ',\n' + ',\n'.join([
            ingest_fields_template.safe_substitute(node_property=node_property, property_ref=property_ref)
            for node_property, property_ref in node_property_map.items()
            if node_property != 'id'  # Make sure to exclude setting the `id` again.
        ])

    # Set extra labels on the node if specified
    if node_extra_labels:
        extra_labels = ':'.join([label for label in node_extra_labels])
        set_clause += f",\n                i:{extra_labels}"
    return set_clause


def _build_rel_properties_statement(rel_var: str, rel_property_map: Dict[str, PropertyRef] = None) -> str:
    set_clause = rel_var + '.lastupdated = {UpdateTag}'
    ingest_fields_template = Template('            $rel_var.$rel_property = $property_ref')

    if rel_property_map:
        set_clause += ',\n' + ',\n'.join([
            ingest_fields_template.safe_substitute(
                rel_var=rel_var,
                rel_property=rel_property,
                property_ref=property_ref,
            )
            for rel_property, property_ref in rel_property_map.items()
        ])
    return set_clause


def _build_attach_sub_resource_statement(sub_resource_link: CartographyLink) -> str:
    """
    Attaches sub resource to node i.
    """
    sub_resource_attach_template = Template("""
        WITH i, item
        MATCH (j:$SubResourceLabel{$SubResourceKey: $SubResourceRef})
        $RelMergeClause
        ON CREATE SET r.firstseen = timestamp()
        SET
            $set_rel_properties_statement
    """)

    if sub_resource_link.direction == LinkDirection.INWARD:
        rel_merge_template = Template("""MERGE (i)<-[r:$SubResourceRelLabel]-(j)""")
    else:
        rel_merge_template = Template("""MERGE (i)-[r:$SubResourceRelLabel]->(j)""")

    rel_merge_clause = rel_merge_template.safe_substitute(SubResourceRelLabel=sub_resource_link.rel_label)

    attach_sub_resource_statement = sub_resource_attach_template.safe_substitute(
        SubResourceLabel=sub_resource_link.label,
        SubResourceKey=sub_resource_link.key,
        SubResourceRef=sub_resource_link.dict_field_ref,
        RelMergeClause=rel_merge_clause,
        SubResourceRelLabel=sub_resource_link.rel_label,
        set_rel_properties_statement=_build_rel_properties_statement('r', sub_resource_link.rel_property_map)
    )
    return attach_sub_resource_statement


def _build_attach_additional_links_statement(additional_links: List[CartographyLink]) -> str:
    """
    Attaches one or more CartographyLinks to node i.
    """
    additional_links_template = Template("""
        WITH i, item
        MATCH ($node_var:$AddlLabel{$AddlKey: $AddlRef})
        $RelMerge
        ON CREATE SET $rel_var.firstseen = timestamp()
        SET
            $set_rel_properties_statement
    """
    )
    links = []
    for num, link in enumerate(additional_links):
        node_var = f"n{num}"
        rel_var = f"r{num}"

        if link.direction == LinkDirection.INWARD:
            rel_merge_template = Template("""MERGE (i)-[$rel_var:$AddlRelLabel]->($node_var)""")
        else:
            rel_merge_template = Template("""MERGE (i)-[$rel_var:$AddlRelLabel]->($node_var)""")

        rel_merge = rel_merge_template.safe_substitute(
            rel_var=rel_var,
            AddlRelLabel=link.rel_label,
            node_var=node_var,
        )

        additional_ref = additional_links_template.safe_substitute(
            AddlLabel=link.label,
            AddlKey=link.key,
            AddlRef=link.dict_field_ref,
            node_var=node_var,
            rel_var=rel_var,
            RelMerge=rel_merge,
            set_rel_properties_statement=_build_rel_properties_statement(rel_var, link.rel_property_map)
        )
        links.append(additional_ref)

    return '\n'.join(links)


def build_ingest_query(
        node_label: str,
        node_property_map: Dict[str, PropertyRef],
        sub_resource_link: CartographyLink,
        additional_links: List[CartographyLink] = None,
        node_extra_labels: List[str] = None,
) -> str:
    query_template = Template("""
    UNWIND {DictList} AS item
        MERGE (i:$node_label{id: item.$dict_id_field})
        ON CREATE SET i.firstseen = timestamp()
        SET 
            $set_node_properties_statement
        $attach_sub_resource_statement
        $attach_additional_links_statement
    """)
    if 'id' not in node_property_map or not node_property_map['id']:
        raise ValueError('node_property_map must have key `id` set.')

    ingest_query = query_template.safe_substitute(
        node_label=node_label,
        dict_id_field=node_property_map['id'],
        set_node_properties_statement=_build_node_properties_statement(node_property_map, node_extra_labels),
        attach_sub_resource_statement=_build_attach_sub_resource_statement(sub_resource_link),
        attach_additional_links_statement=_build_attach_additional_links_statement(additional_links),
    )
    return ingest_query

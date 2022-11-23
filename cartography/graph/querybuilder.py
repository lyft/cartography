import logging
from copy import copy
from dataclasses import asdict
from dataclasses import Field
from dataclasses import field
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef


logger = logging.getLogger(__name__)


def default_field(obj: Any) -> Field:
    """
    Helper function from https://stackoverflow.com/questions/52063759/passing-default-list-argument-to-dataclasses.
    We use this so that we can work around how dataclass fields disallow mutable objects by wrapping them in lambdas.
    Put another way, writing `field(default_factory=lambda: ['Label1', 'Label2'])` is so much more work than writing
    `default_field(['Label1', 'Label2']`.

    Note that if the Field is decorated with @property (like everything in our object model), then we will need to also
    use this technique to correctly implement the setter:
    https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/.

    :param obj: The mutable default object (e.g. a List) that we want to set as a default for a dataclass field.
    :return: A dataclass Field object.
    """
    return field(default_factory=lambda: copy(obj))


def _build_node_properties_statement(
        node_property_map: Dict[str, PropertyRef],
        node_extra_labels: Optional[List[str]],
) -> Optional[str]:
    ingest_fields_template = Template('i.$node_property = $property_ref')
    set_clause = ''

    # If the node_property_map contains more than just `id`, generate a SET statement for the other fields.
    if len(node_property_map.keys()) > 1:
        set_clause += ',\n'.join([
            ingest_fields_template.safe_substitute(node_property=node_property, property_ref=property_ref)
            for node_property, property_ref in node_property_map.items()
            if node_property != 'id'  # Make sure to exclude setting the `id` again.
        ])

    # Set extra labels on the node if specified
    if node_extra_labels:
        extra_labels = ':'.join([label for label in node_extra_labels])
        set_clause += f",\n                i:{extra_labels}"
    return set_clause


def _build_rel_properties_statement(rel_var: str, rel_property_map: Optional[Dict[str, PropertyRef]] = None) -> str:
    set_clause = ''
    ingest_fields_template = Template('$rel_var.$rel_property = $property_ref')

    if rel_property_map:
        set_clause += ',\n'.join([
            ingest_fields_template.safe_substitute(
                rel_var=rel_var,
                rel_property=rel_property,
                property_ref=property_ref,
            )
            for rel_property, property_ref in rel_property_map.items()
        ])
    return set_clause


def _build_attach_sub_resource_statement(sub_resource_link: Optional[CartographyRelSchema]) -> str:
    """
    Attaches sub resource to node i.
    """
    if not sub_resource_link:
        return ''

    sub_resource_attach_template = Template(
        """
        WITH i, item
        MATCH (j:$SubResourceLabel{$SubResourceKey: $SubResourceRef})
        $RelMergeClause
        ON CREATE SET r.firstseen = timestamp()
        SET
            $set_rel_properties_statement
        """,
    )

    if sub_resource_link.direction == LinkDirection.INWARD:
        rel_merge_template = Template("""MERGE (i)<-[r:$SubResourceRelLabel]-(j)""")
    else:
        rel_merge_template = Template("""MERGE (i)-[r:$SubResourceRelLabel]->(j)""")

    rel_merge_clause = rel_merge_template.safe_substitute(SubResourceRelLabel=sub_resource_link.rel_label)

    rel_props_as_dict: Dict[str, PropertyRef] = asdict(sub_resource_link.properties)

    attach_sub_resource_statement = sub_resource_attach_template.safe_substitute(
        SubResourceLabel=sub_resource_link.target_node_label,
        SubResourceKey=sub_resource_link.target_node_key,
        SubResourceRef=sub_resource_link.dict_field_ref,
        RelMergeClause=rel_merge_clause,
        SubResourceRelLabel=sub_resource_link.rel_label,
        set_rel_properties_statement=_build_rel_properties_statement('r', rel_props_as_dict),
    )
    return attach_sub_resource_statement


def _build_attach_additional_links_statement(additional_links: Optional[List[CartographyRelSchema]]) -> str:
    """
    Attaches one or more CartographyRels to node i.
    """
    if not additional_links:
        return ''

    # TODO - support matching on multiple properties
    additional_links_template = Template(
        """
        WITH i, item
        MATCH ($node_var:$AddlLabel{$AddlKey: $AddlRef})
        $RelMerge
        ON CREATE SET $rel_var.firstseen = timestamp()
        SET
            $set_rel_properties_statement
        """,
    )
    links = []
    for num, link in enumerate(additional_links):
        node_var = f"n{num}"
        rel_var = f"r{num}"

        if link.direction == LinkDirection.INWARD:
            rel_merge_template = Template("""MERGE (i)<-[$rel_var:$AddlRelLabel]-($node_var)""")
        else:
            rel_merge_template = Template("""MERGE (i)-[$rel_var:$AddlRelLabel]->($node_var)""")

        rel_merge = rel_merge_template.safe_substitute(
            rel_var=rel_var,
            AddlRelLabel=link.rel_label,
            node_var=node_var,
        )

        # Give a helpful error message when forgetting to put `()` when instantiating a CartographyRelSchema, as this
        # somehow isn't caught by IDEs like PyCharm.
        try:
            rel_props_as_dict: Dict[str, PropertyRef] = asdict(link.properties)
        except TypeError as e:
            if e.args and e.args[0] and e.args == 'asdict() should be called on dataclass instances':
                logger.error(
                    f'TypeError thrown when trying to draw relation "{link.rel_label}" to a "{link.target_node_label}" '
                    f'node. Please make sure that you did not forget to write `()` when specifying `properties` in the'
                    f'dataclass. '
                    f'For example, do `properties: RelProp = RelProp()`; NOT `properties: RelProp = RelProp`.',
                )
            raise

        additional_ref = additional_links_template.safe_substitute(
            AddlLabel=link.target_node_label,
            AddlKey=link.target_node_key,
            AddlRef=link.dict_field_ref,
            node_var=node_var,
            rel_var=rel_var,
            RelMerge=rel_merge,
            set_rel_properties_statement=_build_rel_properties_statement(rel_var, rel_props_as_dict),
        )
        links.append(additional_ref)

    return '\n'.join(links)


def build_ingestion_query(node_schema: CartographyNodeSchema) -> str:
    query_template = Template(
        """
        UNWIND $DictList AS item
            MERGE (i:$node_label{id: $dict_id_field})
            ON CREATE SET i.firstseen = timestamp()
            SET
                $set_node_properties_statement
                $attach_sub_resource_statement
                $attach_additional_links_statement
        """,
    )

    node_props: CartographyNodeProperties = node_schema.properties
    node_props_as_dict: Dict[str, PropertyRef] = asdict(node_props)

    ingest_query = query_template.safe_substitute(
        node_label=node_schema.label,
        dict_id_field=node_props.id,
        set_node_properties_statement=_build_node_properties_statement(node_props_as_dict, node_schema.extra_labels),
        attach_sub_resource_statement=_build_attach_sub_resource_statement(node_schema.subresource_relationship),
        attach_additional_links_statement=_build_attach_additional_links_statement(node_schema.other_relationships),
    )
    return ingest_query

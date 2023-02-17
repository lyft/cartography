import logging
from dataclasses import asdict
from string import Template
from typing import Dict
from typing import Optional
from typing import Set
from typing import Tuple

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import ExtraNodeLabels
from cartography.graph.model import LinkDirection
from cartography.graph.model import OtherRelationships
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher


logger = logging.getLogger(__name__)


def _build_node_properties_statement(
        node_property_map: Dict[str, PropertyRef],
        extra_node_labels: Optional[ExtraNodeLabels] = None,
) -> str:
    """
    Generate a Neo4j clause that sets node properties using the given mapping of attribute names to PropertyRefs.

    As seen in this example,

        node_property_map: Dict[str, PropertyRef] = {
            'id': PropertyRef("Id"),
            'node_prop_1': PropertyRef("Prop1"),
            'node_prop_2': PropertyRef("Prop2", set_in_kwargs=True),
        }
        set_clause: str = _build_node_properties_statement(node_property_map)

    the returned set_clause will be
        ```
        i.id = item.Id,
        i.node_prop_1 = item.Prop1,
        i.node_prop_2 = $Prop2
        ```
    where `i` is a reference to the Neo4j node.
    :param node_property_map: Mapping of node attribute names as str to PropertyRef objects
    :param extra_node_labels: Optional ExtraNodeLabels object to set on the node as string
    :return: The resulting Neo4j SET clause to set the given attributes on the node
    """
    ingest_fields_template = Template('i.$node_property = $property_ref')

    set_clause = ',\n'.join([
        ingest_fields_template.safe_substitute(node_property=node_property, property_ref=property_ref)
        for node_property, property_ref in node_property_map.items()
        if node_property != 'id'  # The `MERGE` clause will have already set `id`; let's not set it again.
    ])

    # Set extra labels on the node if specified
    if extra_node_labels:
        extra_labels = ':'.join([label for label in extra_node_labels.labels])
        set_clause += f",\n                i:{extra_labels}"
    return set_clause


def _build_rel_properties_statement(rel_var: str, rel_property_map: Optional[Dict[str, PropertyRef]] = None) -> str:
    """
    Generate a Neo4j clause that sets relationship properties using the given mapping of attribute names to
    PropertyRefs.

    In this code example:

        rel_property_map: Dict[str, PropertyRef] = {
            'rel_prop_1': PropertyRef("Prop1"),
            'rel_prop_2': PropertyRef("Prop2", static=True),
        }
        set_clause: str = _build_rel_properties_statement('r', rel_property_map)

    the returned set_clause will be:

        r.rel_prop_1 = item.Prop1,
        r.rel_prop_2 = $Prop2

    :param rel_var: The variable name to use for the relationship in the Neo4j query
    :param rel_property_map: Mapping of relationship attribute names as str to PropertyRef objects
    :return: The resulting Neo4j SET clause to set the given attributes on the relationship
    """
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


def _build_match_clause(matcher: TargetNodeMatcher) -> str:
    """
    Generate a Neo4j match statement on one or more keys and values for a given node.
    :param matcher: A TargetNodeMatcher object
    :return: a Neo4j match clause
    """
    match = Template("$Key: $PropRef")
    matcher_asdict = asdict(matcher)
    return ', '.join(match.safe_substitute(Key=key, PropRef=prop_ref) for key, prop_ref in matcher_asdict.items())


def _asdict_with_validate_relprops(link: CartographyRelSchema) -> Dict[str, PropertyRef]:
    """
    Give a helpful error message when forgetting to put `()` when instantiating a CartographyRelSchema, as this
    isn't always caught by IDEs.
    """
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
    return rel_props_as_dict


def _build_attach_sub_resource_statement(sub_resource_link: Optional[CartographyRelSchema] = None) -> str:
    """
    Generates a Neo4j statement to attach a sub resource to a node. A 'sub resource' is a term we made up to describe
    billing units of a given resource. For example,
    - In AWS, the sub resource is an AWSAccount.
    - In Azure, the sub resource is a Subscription.
    - In GCP, the sub resource is a GCPProject.
    - etc.
    This is a private function not meant to be called outside of build_ingest_query().
    :param sub_resource_link: Optional: The CartographyRelSchema object connecting previous node(s) to the sub resource.
    :return: a Neo4j clause that connects previous node(s) to a sub resource, taking into account the labels, attribute
    keys, and directionality. If sub_resource_link is None, return an empty string.
    """
    if not sub_resource_link:
        return ''

    sub_resource_attach_template = Template(
        """
        OPTIONAL MATCH (j:$SubResourceLabel{$MatchClause})
        WITH i, item, j WHERE j IS NOT NULL
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

    rel_props_as_dict: Dict[str, PropertyRef] = _asdict_with_validate_relprops(sub_resource_link)

    attach_sub_resource_statement = sub_resource_attach_template.safe_substitute(
        SubResourceLabel=sub_resource_link.target_node_label,
        MatchClause=_build_match_clause(sub_resource_link.target_node_matcher),
        RelMergeClause=rel_merge_clause,
        SubResourceRelLabel=sub_resource_link.rel_label,
        set_rel_properties_statement=_build_rel_properties_statement('r', rel_props_as_dict),
    )
    return attach_sub_resource_statement


def _build_attach_additional_links_statement(
        additional_relationships: Optional[OtherRelationships] = None,
) -> str:
    """
    Generates a Neo4j statement to attach one or more CartographyRelSchemas to node(s) previously mentioned in the
    query.
    This is a private function not meant to be called outside of build_ingestion_query().
    :param additional_relationships: Optional list of CartographyRelSchema describing what other relationships should
    be created from the previous node(s) in this query.
    :return: A Neo4j clause that connects previous node(s) to the given additional_links., taking into account the
    labels, attribute keys, and directionality. If additional_relationships is None, return an empty string.
    """
    if not additional_relationships:
        return ''

    additional_links_template = Template(
        """
        WITH i, item
        OPTIONAL MATCH ($node_var:$AddlLabel{$MatchClause})
        WITH i, item, $node_var WHERE $node_var IS NOT NULL
        $RelMerge
        ON CREATE SET $rel_var.firstseen = timestamp()
        SET
            $set_rel_properties_statement
        """,
    )
    links = []
    for num, link in enumerate(additional_relationships.rels):
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

        rel_props_as_dict = _asdict_with_validate_relprops(link)

        additional_ref = additional_links_template.safe_substitute(
            AddlLabel=link.target_node_label,
            MatchClause=_build_match_clause(link.target_node_matcher),
            node_var=node_var,
            rel_var=rel_var,
            RelMerge=rel_merge,
            set_rel_properties_statement=_build_rel_properties_statement(rel_var, rel_props_as_dict),
        )
        links.append(additional_ref)

    return 'UNION'.join(links)


def _build_attach_relationships_statement(
        sub_resource_relationship: Optional[CartographyRelSchema],
        other_relationships: Optional[OtherRelationships],
) -> str:
    """
    Use Neo4j subqueries to attach sub resource and/or other relationships.
    Subqueries allow the query to continue to run even if we only have data for some but not all the relationships
    defined by a schema.
    For example, if an EC2Instance has attachments to NetworkInterfaces and AWSAccounts, but our data only includes
    EC2Instance to AWSAccount information, structuring the ingestion query with subqueries allows us to build a query
    that will ignore the null relationships and continue to MERGE the ones that exist.
    """
    if not sub_resource_relationship and not other_relationships:
        return ""

    attach_sub_resource_statement = _build_attach_sub_resource_statement(sub_resource_relationship)
    attach_additional_links_statement = _build_attach_additional_links_statement(other_relationships)

    statements = []
    statements += [attach_sub_resource_statement] if attach_sub_resource_statement else []
    statements += [attach_additional_links_statement] if attach_additional_links_statement else []

    attach_relationships_statement = 'UNION'.join(stmt for stmt in statements)

    query_template = Template(
        """
        WITH i, item
        CALL {
            WITH i, item
            $attach_relationships_statement
        }
        """,
    )
    return query_template.safe_substitute(attach_relationships_statement=attach_relationships_statement)


def _filter_selected_relationships(
        node_schema: CartographyNodeSchema,
        selected_relationships: Set[CartographyRelSchema],
) -> Tuple[Optional[CartographyRelSchema], Optional[OtherRelationships]]:
    """
    Ensures that selected relationships specified to build_ingestion_query() are actually present on
    node_schema.sub_resource_relationship and node_schema.other_relationships.
    :param node_schema: The node schema object to filter relationships against
    :param selected_relationships: The set of relationships to check if they exist in the node schema. If empty set,
    this means that no relationships have been selected. None is not an accepted value here.
    :return: a tuple of the (sub resource rel [if present in selected_relationships], an OtherRelationships object
    containing all values of node_schema.other_relationships that are present in selected_relationships)
    """
    # The empty set means no relationships are selected
    if selected_relationships == set():
        return None, None

    # Collect the node's sub resource rel and OtherRelationships together in one set for easy comparison
    all_rels_on_node = {node_schema.sub_resource_relationship}
    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            all_rels_on_node.add(rel)

    # Ensure that the selected_relationships are actually present on the node_schema.
    for selected_rel in selected_relationships:
        if selected_rel not in all_rels_on_node:
            raise ValueError(
                f"build_ingestion_query() failed: CartographyRelSchema {selected_rel.__class__.__name__} is not "
                f"defined on CartographyNodeSchema type {node_schema.__class__.__name__}. Please verify the "
                f"value of `selected_relationships` passed to `build_ingestion_query()`.",
            )

    sub_resource_rel = node_schema.sub_resource_relationship
    if sub_resource_rel not in selected_relationships:
        sub_resource_rel = None

    # By this point, everything in selected_relationships is validated to be present in node_schema
    filtered_other_rels = OtherRelationships([rel for rel in selected_relationships if rel != sub_resource_rel])

    return sub_resource_rel, filtered_other_rels


def build_ingestion_query(
        node_schema: CartographyNodeSchema,
        selected_relationships: Optional[Set[CartographyRelSchema]] = None,
) -> str:
    """
    Generates a Neo4j query from the given CartographyNodeSchema to ingest the specified nodes and relationships so that
    cartography module authors don't need to handwrite their own queries.
    :param node_schema: The CartographyNodeSchema object to build a Neo4j query from.
    :param selected_relationships: If specified, generates a query that attaches only the relationships in this optional
    set of CartographyRelSchema. The RelSchema specified here _must_ be present in node_schema.sub_resource_relationship
    or node_schema.other_relationships.
    If selected_relationships is None (default), then we create a query using all RelSchema specified in
    node_schema.sub_resource_relationship + node_schema.other_relationships.
    If selected_relationships is the empty set, we create a query with no relationship attachments at all.
    :return: An optimized Neo4j query that can be used to ingest nodes and relationships.
    Important notes:
    - The resulting query uses the UNWIND + MERGE pattern (see
      https://neo4j.com/docs/cypher-manual/current/clauses/unwind/#unwind-creating-nodes-from-a-list-parameter) to batch
      load the data for speed.
    - The query assumes that a list of dicts will be passed to it through parameter $DictList.
    - The query sets `firstseen` attributes on all the nodes and relationships that it creates.
    - The query is intended to be supplied as input to cartography.core.client.tx.load_graph_data().
    """
    query_template = Template(
        """
        UNWIND $DictList AS item
            MERGE (i:$node_label{id: $dict_id_field})
            ON CREATE SET i.firstseen = timestamp()
            SET
                $set_node_properties_statement
            $attach_relationships_statement
        """,
    )

    node_props: CartographyNodeProperties = node_schema.properties
    node_props_as_dict: Dict[str, PropertyRef] = asdict(node_props)

    # Handle selected relationships
    sub_resource_rel: Optional[CartographyRelSchema] = node_schema.sub_resource_relationship
    other_rels: Optional[OtherRelationships] = node_schema.other_relationships
    if selected_relationships or selected_relationships == set():
        sub_resource_rel, other_rels = _filter_selected_relationships(node_schema, selected_relationships)

    ingest_query = query_template.safe_substitute(
        node_label=node_schema.label,
        dict_id_field=node_props.id,
        set_node_properties_statement=_build_node_properties_statement(
            node_props_as_dict,
            node_schema.extra_node_labels,
        ),
        attach_relationships_statement=_build_attach_relationships_statement(sub_resource_rel, other_rels),
    )
    return ingest_query

from dataclasses import asdict
from string import Template
from typing import List
from typing import Optional
from typing import Set

from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import _build_match_clause
from cartography.graph.querybuilder import filter_selected_relationships
from cartography.graph.querybuilder import rel_present_on_node_schema


def build_cleanup_queries(
        node_schema: CartographyNodeSchema,
        selected_rels: Optional[Set[CartographyRelSchema]] = None,
) -> List[str]:
    """
    Generates queries to clean up stale nodes and relationships from the given CartographyNodeSchema.
    :param node_schema: The given CartographyNodeSchema to generate cleanup queries for.
    :param selected_rels: Optional. If specified, only generate cleanup queries bound to the given set of selected
    relationships. If not specified, generated cleanup queries against all relationships on the node_schema.
    :return: A list of Neo4j queries to clean up nodes and relationships. Order matters: we always clean up the sub
    resource relationship last because we only clean up stale nodes and rels that are associated with a given sub
    resource, so if we delete the sub resource first then we will not be able to reach the stale nodes and rels, thus
    leaving orphaned objects behind.
    Note also that we return the empty list if the node_schema has no relationships. Doing cleanups of nodes without
    relationships can be resource expensive for a large graph, and you might risk deleting unintended objects. Please
    write a manual cleanup job if you wish to do this.
    """
    other_rels = node_schema.other_relationships
    sub_resource_rel = node_schema.sub_resource_relationship

    if selected_rels:
        # Ensure that the selected rels actually exist on the node_schema
        sub_resource_rel, other_rels = filter_selected_relationships(node_schema, selected_rels)

    if not sub_resource_rel:
        raise ValueError(
            "Auto-creating a cleanup job for a node_schema without a sub resource relationship is not supported. "
            f'Please check the class definition of "{node_schema.__class__.__name__}". If the optional `selected_rels` '
            'param was specified to build_cleanup_queries(), then ensure that the sub resource relationship is '
            'present.',
        )

    result = []
    if other_rels:
        for rel in other_rels.rels:
            result.append(
                _build_cleanup_node_query(node_schema, rel),
            )
            result.append(
                _build_cleanup_rel_query(node_schema, rel),
            )

    if sub_resource_rel:
        # Make sure that the sub resource one is last in the list; order matters.
        result.append(
            _build_cleanup_node_query(node_schema),
        )
        result.append(
            _build_cleanup_rel_query(node_schema),
        )
    # Note that auto-cleanups for a node with no relationships does not happen at all - we don't support it.
    return result


def _build_cleanup_node_query(
        node_schema: CartographyNodeSchema,
        selected_relationship: Optional[CartographyRelSchema] = None,
) -> str:
    """
    Generates an optimized and tuned node deletion query for the given node schema. Ensures that the node type to be
    cleaned up is connected to a sub resource, and (optionally) to another relationship -- this way it is much less
    likely to delete nodes that you weren't expecting.
    :param node_schema: The node_schema to generate a query from.
    :param selected_relationship: If specified, generate a cleanup query for the node_schema and the given
    selected_relationship. selected_relationship must be in the set {node_schema.sub_resource_relationship} +
    node_schema.other_relationships. If not specified, this defaults to the sub resource relationship.
    :return: A Neo4j query to clean up stale nodes of the given type.
    """
    # Validation
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"_build_cleanup_node_query() failed: '{node_schema.label}' does not have a sub_resource_relationship "
            "defined, so we cannot generate a query to clean it up. Please verify that the class definition is what "
            "you expect.",
        )
    if selected_relationship and not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError(
            f"_build_cleanup_node_query(): Attempted to build cleanup query for node '{node_schema.label}' and "
            f"relationship {selected_relationship.rel_label} but that relationship is not present on the node. Please "
            "verify the node class definition for the relationships that it has.",
        )

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_resource_link_template = Template("<-[:$SubResourceRelLabel]-")
    else:
        sub_resource_link_template = Template("-[:$SubResourceRelLabel]->")
    sub_resource_link = sub_resource_link_template.safe_substitute(
        SubResourceRelLabel=node_schema.sub_resource_relationship.rel_label,
    )

    # Make query to consider just the sub resource and nothing else
    if not selected_relationship or selected_relationship == node_schema.sub_resource_relationship:
        return _build_cleanup_node_sub_resource_only(
            node_schema,
            sub_resource_link,
            node_schema.sub_resource_relationship.target_node_matcher,
        )

    # Draw selected relationship with correct direction
    if selected_relationship.direction == LinkDirection.INWARD:
        selected_rel_template = Template("<-[:$SelectedRelLabel]-")
    else:
        selected_rel_template = Template("-[:$SelectedRelLabel]->")
    selected_rel = selected_rel_template.safe_substitute(SelectedRelLabel=selected_relationship.rel_label)

    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        MATCH (n:$node_label)$sub_resource_link(:$sub_resource_label{$match_sub_res_clause})
        MATCH (n)$selected_rel(:$other_node_label)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_link=sub_resource_link,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        match_sub_res_clause=_build_match_clause(node_schema.sub_resource_relationship.target_node_matcher),
        selected_rel=selected_rel,
        other_node_label=selected_relationship.target_node_label,
    )


def _build_cleanup_node_sub_resource_only(
        node_schema: CartographyNodeSchema,
        sub_res_link: str,
        sub_res_node_matcher: TargetNodeMatcher,
) -> str:
    """
    Generate a query to clean up a node attached to a sub resource.
    :param node_schema: The CartographyNodeSchema object
    :param sub_res_link: A string that looks like "<-[:RELATIONSHIP]-" or "-[:RELATIONSHIP]->"
    :param sub_res_node_matcher: The TargetNodeMatcher object used to determine which sub resource to query for when
    cleaning up.
    """
    query_template = Template(
        """
        MATCH (n:$node_label)$sub_res_link(:$sub_resource_label{$sub_res_match_clause})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
    )
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"'_build_cleanup_node_sub_resource_only() failed: {node_schema.label}' does not have a "
            "sub_resource_relationship defined, so we cannot generate a query to clean it up. Please verify that the "
            "class definition is what you expect.",
        )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        sub_res_link=sub_res_link,
        sub_res_match_clause=_build_match_clause(sub_res_node_matcher),
    )


def _build_cleanup_rel_query(
        node_schema: CartographyNodeSchema,
        selected_relationship: Optional[CartographyRelSchema] = None,
) -> str:
    """
    Generates an optimized and tuned relationship deletion query for the given node schema.
    Ensures that the node-relationship to be cleaned up is connected to a given sub resource, and (optionally) to
    another relationship -- this way it is much less likely to delete relationships that you weren't expecting.
    :param node_schema: The node_schema to generate a query from.
    :param selected_relationship: If specified, generate a cleanup query for the node_schema and the given
    selected_relationship. selected_relationship must be in the set {node_schema.sub_resource_relationship} +
    node_schema.other_relationships. If not specified, this defaults to the sub resource relationship.
    :return: A Neo4j query to clean up stale relationships of the given type in the given node_schema.
    """
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"_build_cleanup_rel_query() failed: '{node_schema.label}' does not have a sub_resource_relationship "
            "defined, so we cannot generate a query to clean up rels. Please verify that the class definition is what "
            "you expect. If this is intended, then please write a manual cleanup job in json as auto cleanup jobs "
            "without sub resource rels is currently not supported.",
        )
    # Make query to consider just the sub resource and nothing else
    if not selected_relationship:
        return _build_cleanup_rel_sub_resource_only(node_schema)

    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError(
            f"_build_cleanup_rel_query(): Attempted to build cleanup query for node '{node_schema.label}' and "
            f"relationship {selected_relationship.rel_label} but that relationship is not present on the node. Please "
            f"verify the node class definition for the relationships that it has.",
        )

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_resource_link_template = Template("<-[:$SubRelLabel]-")
    else:
        sub_resource_link_template = Template("-[:$SubRelLabel]->")
    sub_resource_link = sub_resource_link_template.safe_substitute(
        SubRelLabel=node_schema.sub_resource_relationship.rel_label,
    )

    # Draw selected relationship with correct direction
    if selected_relationship.direction == LinkDirection.INWARD:
        rel_to_delete_template = Template("<-[r:$RelToDeleteLabel]-")
    else:
        rel_to_delete_template = Template("-[r:$RelToDeleteLabel]->")
    rel_to_delete = rel_to_delete_template.safe_substitute(RelToDeleteLabel=selected_relationship.rel_label)

    # Ensure the node is attached to the sub resource and delete the relationship
    query_template = Template(
        """
        MATCH (src:$node_label)$sub_resource_link(:$sub_resource_label{$match_sub_res_clause})
        MATCH (src)$rel_to_delete(:$other_node)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_link=sub_resource_link,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        match_sub_res_clause=_build_match_clause(node_schema.sub_resource_relationship.target_node_matcher),
        rel_to_delete=rel_to_delete,
        other_node=selected_relationship.target_node_label,
    )


def _validate_target_node_matcher_for_cleanup_job(tgm: TargetNodeMatcher):
    tgm_asdict = asdict(tgm)

    for key, prop_ref in tgm_asdict.items():
        if not prop_ref.set_in_kwargs:
            raise ValueError(
                f"TargetNodeMatcher PropertyRefs in the sub_resource_relationship must have set_in_kwargs=True. "
                f"{key} has set_in_kwargs=False, please check.",
            )


def _build_cleanup_rel_sub_resource_only(node_schema: CartographyNodeSchema) -> str:
    """
    Generate a query to clean up stale relationships between nodes and their sub resource.
    :param node_schema: The CartographyNodeSchema object
    """
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"_build_cleanup_rel_sub_resource_only() failed: {node_schema.label}' does not have a "
            "sub_resource_relationship defined, so we cannot generate a query to clean it up. Please verify that the "
            "class definition is what you expect.",
        )
    _validate_target_node_matcher_for_cleanup_job(node_schema.sub_resource_relationship.target_node_matcher)

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_resource_link_template = Template("<-[r:$SubRelLabel]-")
    else:
        sub_resource_link_template = Template("-[r:$SubRelLabel]->")
    sub_resource_link = sub_resource_link_template.safe_substitute(
        SubRelLabel=node_schema.sub_resource_relationship.rel_label,
    )

    query_template = Template(
        """
        MATCH (:$node_label)$sub_resource_link(:$sub_resource_label{$sub_res_match_clause})
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        sub_resource_link=sub_resource_link,
        sub_res_match_clause=_build_match_clause(node_schema.sub_resource_relationship.target_node_matcher),
    )

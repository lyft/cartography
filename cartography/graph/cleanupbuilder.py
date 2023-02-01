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
    :param selected_rels: Optional. If specified, only generate cleanup queries where the `node_schema` is bound to this
    given set of selected relationships. Raises an exception if any of the rels in `selected_rels` aren't actually
    defined on the `node_schema`.
    If `selected_rels` is not specified (default), we generate cleanup queries against all relationships defined on the
    `node_schema`.
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
            result.extend(_build_cleanup_node_and_rel_queries(node_schema, rel))

    # Make sure that the sub resource cleanup job is last in the list; order matters.
    result.extend(_build_cleanup_node_and_rel_queries(node_schema, sub_resource_rel))
    # Note that auto-cleanups for a node with no relationships does not happen at all - we don't support it.
    return result


def _build_cleanup_node_and_rel_queries(
        node_schema: CartographyNodeSchema,
        selected_relationship: CartographyRelSchema,
) -> List[str]:
    """
    Private function that performs the main string template logic for generating cleanup node and relationship queries.
    :param node_schema: The given CartographyNodeSchema to generate cleanup queries for.
    :param selected_relationship: Determines what relationship on the node_schema to build cleanup queries for.
    selected_relationship must be in the set {node_schema.sub_resource_relationship} + node_schema.other_relationships.
    :return: A list of 2 cleanup queries. The first one cleans up stale nodes attached to the given
    selected_relationships, and the second one cleans up stale selected_relationships. For example outputs, see
    tests.unit.cartography.graph.test_cleanupbuilder.
    """
    if not node_schema.sub_resource_relationship:
        raise ValueError(
            f"_build_cleanup_node_query() failed: '{node_schema.label}' does not have a sub_resource_relationship "
            "defined, so we cannot generate a query to clean it up. Please verify that the class definition is what "
            "you expect.",
        )
    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError(
            f"_build_cleanup_node_query(): Attempted to build cleanup query for node '{node_schema.label}' and "
            f"relationship {selected_relationship.rel_label} but that relationship is not present on the node. Please "
            "verify the node class definition for the relationships that it has.",
        )

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_resource_link_template = Template("<-[s:$SubResourceRelLabel]-")
    else:
        sub_resource_link_template = Template("-[s:$SubResourceRelLabel]->")
    sub_resource_link = sub_resource_link_template.safe_substitute(
        SubResourceRelLabel=node_schema.sub_resource_relationship.rel_label,
    )

    # The cleanup node query must always be before the cleanup rel query
    delete_action_clauses = [
        """
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
    ]
    # Now clean up the relationships
    if selected_relationship == node_schema.sub_resource_relationship:
        _validate_target_node_matcher_for_cleanup_job(node_schema.sub_resource_relationship.target_node_matcher)
        delete_action_clauses.append(
            """
            WHERE s.lastupdated <> $UPDATE_TAG
            WITH s LIMIT $LIMIT_SIZE
            DELETE s;
            """,
        )
    else:
        delete_action_clauses.append(
            """
            WHERE r.lastupdated <> $UPDATE_TAG
            WITH r LIMIT $LIMIT_SIZE
            DELETE r;
            """,
        )

    # Ensure the node is attached to the sub resource and delete the node
    query_template = Template(
        """
        MATCH (n:$node_label)$sub_resource_link(:$sub_resource_label{$match_sub_res_clause})
        $selected_rel_clause
        $delete_action_clause
        """,
    )
    return [
        query_template.safe_substitute(
            node_label=node_schema.label,
            sub_resource_link=sub_resource_link,
            sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
            match_sub_res_clause=_build_match_clause(node_schema.sub_resource_relationship.target_node_matcher),
            selected_rel_clause=(
                "" if selected_relationship == node_schema.sub_resource_relationship
                else _build_selected_rel_clause(selected_relationship)
            ),
            delete_action_clause=delete_action_clause,
        ) for delete_action_clause in delete_action_clauses
    ]


def _build_selected_rel_clause(selected_relationship: CartographyRelSchema) -> str:
    """
    Draw selected relationship with correct direction. Returns a string that looks like either
    MATCH (n)<-[r:$SelectedRelLabel]-(:$other_node_label) or
    MATCH (n)-[r:$SelectedRelLabel]->(:$other_node_label)
    """
    if selected_relationship.direction == LinkDirection.INWARD:
        selected_rel_template = Template("<-[r:$SelectedRelLabel]-")
    else:
        selected_rel_template = Template("-[r:$SelectedRelLabel]->")
    selected_rel = selected_rel_template.safe_substitute(SelectedRelLabel=selected_relationship.rel_label)
    selected_rel_clause_template = Template("""MATCH (n)$selected_rel(:$other_node_label)""")
    selected_rel_clause = selected_rel_clause_template.safe_substitute(
        selected_rel=selected_rel,
        other_node_label=selected_relationship.target_node_label,
    )
    return selected_rel_clause


def _validate_target_node_matcher_for_cleanup_job(tgm: TargetNodeMatcher):
    """
    Raises ValueError if a single PropertyRef in the given TargetNodeMatcher does not have set_in_kwargs=True.
    Auto cleanups require the sub resource target node matcher to have set_in_kwargs=True because the GraphJob
    class injects the sub resource id via a query kwarg parameter. See GraphJob and GraphStatement classes.
    This is a private function meant only to be called when we clean up the sub resource relationship.
    """
    tgm_asdict = asdict(tgm)

    for key, prop_ref in tgm_asdict.items():
        if not prop_ref.set_in_kwargs:
            raise ValueError(
                f"TargetNodeMatcher PropertyRefs in the sub_resource_relationship must have set_in_kwargs=True. "
                f"{key} has set_in_kwargs=False, please check.",
            )

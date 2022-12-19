from string import Template
from typing import Optional

from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import _build_match_clause
from cartography.graph.querybuilder import rel_present_on_node_schema


def build_cleanup_queries(node_schema: CartographyNodeSchema) -> list[str]:
    result = []
    if node_schema.other_relationships:
        for rel in node_schema.other_relationships.rels:
            result.append(
                build_cleanup_node_query(node_schema, rel.target_node_matcher, rel),
            )
            result.append(
                build_cleanup_rel_query(node_schema, rel.target_node_matcher, rel),
            )

    if node_schema.sub_resource_relationship:
        # Make sure that the sub resource one is last in the list; order matters.
        result.append(
            build_cleanup_node_query(node_schema, node_schema.sub_resource_relationship.target_node_matcher),
        )
        result.append(
            build_cleanup_rel_query(node_schema, node_schema.sub_resource_relationship.target_node_matcher),
        )
    # Cleanup does not happen for a node with no relationships
    return result


def _build_cleanup_node_sub_resource_only(
        node_schema: CartographyNodeSchema,
        sub_res_link: str,
        sub_res_node_matcher: TargetNodeMatcher,
) -> str:
    query_template = Template(
        """
        MATCH (n:$node_label)$sub_rel_link(:$sub_resource_label{$sub_res_match_clause})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
        """,
    )
    if not node_schema.sub_resource_relationship:
        raise ValueError("TODO")  # TODO
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_label=node_schema.sub_resource_relationship.rel_label,
        sub_rel_link=sub_res_link,
        sub_rel_label=node_schema.sub_resource_relationship.rel_label,
        sub_res_match_clause=_build_match_clause(sub_res_node_matcher),
    )


def build_cleanup_node_query(
        node_schema: CartographyNodeSchema,
        sub_resource_node_matcher: TargetNodeMatcher,
        selected_relationship: Optional[CartographyRelSchema] = None,
) -> str:
    if not node_schema.sub_resource_relationship:
        raise ValueError("TODO")  # TODO make a good err message here

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_rel_link_template = Template("<-[:$SubRelLabel]-")
    else:
        sub_rel_link_template = Template("-[:$SubRelLabel]->")
    sub_rel_link = sub_rel_link_template.safe_substitute(SubRelLabel=node_schema.sub_resource_relationship.rel_label)

    # Make query to consider just the sub resource and nothing else
    if not selected_relationship:
        return _build_cleanup_node_sub_resource_only(node_schema, sub_rel_link, sub_resource_node_matcher)

    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError("TODO")  # TODO make a good err message here

    # Draw selected relationship with correct direction
    if selected_relationship.direction == LinkDirection.INWARD:
        rel_to_delete_template = Template("<-[:$RelToDeleteLabel]-")
    else:
        rel_to_delete_template = Template("-[:$RelToDeleteLabel]->")
    rel_to_delete = rel_to_delete_template.safe_substitute(RelToDeleteLabel=selected_relationship.rel_label)

    # Ensure the node is attached to the sub resource
    # Delete the node
    query_template = Template(
        """
    MATCH (src:$node_label)$sub_rel_link(:$sub_resource_label{$match_sub_res_clause})
    MATCH (src)$rel_to_delete(n:$node_to_delete)
    WHERE n.lastupdated <> $UPDATE_TAG
    WITH n LIMIT $LIMIT_SIZE
    DETACH DELETE n;
    """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_rel_link=sub_rel_link,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        match_sub_res_clause=_build_match_clause(sub_resource_node_matcher),
        rel_to_delete=rel_to_delete,
        node_to_delete=selected_relationship.target_node_label,
    )


def _build_cleanup_rel_sub_resource_only(
        node_schema: CartographyNodeSchema,
        sub_res_node_matcher: TargetNodeMatcher,
) -> str:
    if not node_schema.sub_resource_relationship:
        raise ValueError("TODO")  # TODO error message

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_rel_link_template = Template("<-[r:$SubRelLabel]-")
    else:
        sub_rel_link_template = Template("-[r:$SubRelLabel]->")
    sub_res_link = sub_rel_link_template.safe_substitute(SubRelLabel=node_schema.sub_resource_relationship.rel_label)

    query_template = Template(
        """
        MATCH (:$node_label)$sub_res_link(:$sub_resource_label{$sub_res_match_clause})
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        sub_res_link=sub_res_link,
        sub_rel_label=node_schema.sub_resource_relationship.rel_label,
        sub_res_match_clause=_build_match_clause(sub_res_node_matcher),
    )


def build_cleanup_rel_query(
        node_schema: CartographyNodeSchema,
        sub_resource_node_matcher: TargetNodeMatcher,
        selected_relationship: Optional[CartographyRelSchema] = None,
) -> str:
    if not node_schema.sub_resource_relationship:
        raise ValueError("TODO")  # TODO make a good err message here

    # Make query to consider just the sub resource and nothing else
    if not selected_relationship:
        return _build_cleanup_rel_sub_resource_only(node_schema, sub_resource_node_matcher)

    if not rel_present_on_node_schema(node_schema, selected_relationship):
        raise ValueError("TODO")  # TODO make a good err message here

    # Draw sub resource rel with correct direction
    if node_schema.sub_resource_relationship.direction == LinkDirection.INWARD:
        sub_rel_link_template = Template("<-[:$SubRelLabel]-")
    else:
        sub_rel_link_template = Template("-[:$SubRelLabel]->")
    sub_rel_link = sub_rel_link_template.safe_substitute(SubRelLabel=node_schema.sub_resource_relationship.rel_label)

    # Draw selected relationship with correct direction
    if selected_relationship.direction == LinkDirection.INWARD:
        rel_to_delete_template = Template("<-[r:$RelToDeleteLabel]-")
    else:
        rel_to_delete_template = Template("-[r:$RelToDeleteLabel]->")
    rel_to_delete = rel_to_delete_template.safe_substitute(RelToDeleteLabel=selected_relationship.rel_label)

    # Ensure the node is attached to the sub resource and delete the relationship
    query_template = Template(
        """
    MATCH (src:$node_label)$sub_rel_link(:$sub_resource_label{$match_sub_res_clause})
    MATCH (src)$rel_to_delete(n:$node_to_delete)
    WHERE r.lastupdated <> $UPDATE_TAG
    WITH r LIMIT $LIMIT_SIZE
    DELETE r;
    """,
    )
    return query_template.safe_substitute(
        node_label=node_schema.label,
        sub_rel_link=sub_rel_link,
        sub_resource_label=node_schema.sub_resource_relationship.target_node_label,
        match_sub_res_clause=_build_match_clause(sub_resource_node_matcher),
        rel_to_delete=rel_to_delete,
        node_to_delete=selected_relationship.target_node_label,
    )

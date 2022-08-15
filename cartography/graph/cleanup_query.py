from typing import List
from string import Template


def build_cleanup_queries(
        node_label: str,
        rel_label: str,
        sub_resource_label: str,
        sub_resource_value: str,
        sub_resource_key: str = None,
        cleanup_rel: bool = True,
) -> List[str]:
    # Convention: we must always point from the sub resource out to the resource.
    node_cleanup_query_template = Template(
        """
        MATCH (n:$node_label)<-[:$rel_label]-(:$sub_resource_label{$sub_resource_key: {$sub_resource_value}})
        WHERE n.lastupdated <> {UPDATE_TAG}
        WITH n
        LIMIT {LIMIT_SIZE} 
        DETACH DELETE (n)
        """
    )
    if not sub_resource_key:
        sub_resource_key = 'id'

    node_cleanup_query = node_cleanup_query_template.safe_substitute(
        node_label=node_label,
        rel_label=rel_label,
        sub_resource_key=sub_resource_key,
        sub_resource_label=sub_resource_label,
        sub_resource_value=sub_resource_value,
    )

    result = [node_cleanup_query]
    if cleanup_rel:
        rel_cleanup_query_template = Template(
            """
            MATCH (:$node_label)<-[r:$rel_label]-(:$sub_resource_label{$sub_resource_key: {$sub_resource_value}})
            WHERE r.lastupdated <> {UPDATE_TAG}
            WITH r LIMIT {LIMIT_SIZE}
            DELETE r
            """
        )
        rel_cleanup_query = rel_cleanup_query_template.safe_substitute(
            node_label=node_label,
            rel_label=rel_label,
            sub_resource_label=sub_resource_label,
            sub_resource_key=sub_resource_key,
            sub_resource_value=sub_resource_value,
        )
        result.append(rel_cleanup_query)

    return result


def build_remove_attribute_query(
        attribute_name: str,
        node_label: str,
        rel_label: str,
        sub_resource_label: str,
        sub_resource_value: str,
        sub_resource_key: str = None,
) -> str:
    attribute_removal_template = Template(
        """
        MATCH (n:$node_label)<-[:$rel_label]-(:$sub_resource_label{$sub_resource_key: $sub_resource_value})
        WHERE EXISTS (n.$attribute_name)
        REMOVE n.$attribute_name
        """
    )
    if not sub_resource_key:
        sub_resource_key = 'id'

    return attribute_removal_template.safe_substitute(
        node_label=node_label,
        rel_label=rel_label,
        sub_resource_label=sub_resource_label,
        sub_resource_key=sub_resource_key,
        sub_resource_value=sub_resource_value,
        attribute_name=attribute_name,
    )
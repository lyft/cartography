import logging
from typing import Dict
from typing import List

import neo4j

from cartography.graph.querybuilder import build_node_ingestion_query
from cartography.graph.querybuilder import build_relationship_ingestion_query

logger = logging.getLogger(__name__)


def merge_nodes_with_unwind(
    tx: neo4j.Transaction, node_label: str, node_property_map: Dict[str, str],
    node_data_list: List[Dict], update_tag: int, batch_size: int = 1000,
) -> None:
    if batch_size < 1:
        raise ValueError("batch_size cannot be less than 1.")

    ingest_query = build_node_ingestion_query(node_label, node_property_map)

    chunk = node_data_list[:batch_size]
    cursor = 0
    while len(chunk) > 0:
        query_args = {
            'UpdateTag': update_tag,
            'DictList': chunk,
        }
        try:
            tx.run(ingest_query, **query_args)
        except neo4j.ServiceUnavailable:
            logger.error("Failed to merge nodes.", exc_info=True)
            tx.rollback()
            raise
        cursor += batch_size
        chunk = node_data_list[cursor:cursor + batch_size]


def merge_relationships_with_unwind(
    tx: neo4j.Transaction, node_label_a: str, search_property_a: str, dict_key_a: str,
    node_label_b: str, search_property_b: str, dict_key_b: str,
    relationship_label: str,
    rel_mapping_list: List[Dict],
    update_tag: int,
    batch_size: int = 1000,
    rel_property_map: Dict[str, str] = None,
) -> None:
    if batch_size < 1:
        raise ValueError("batch_size cannot be less than 1.")

    query = build_relationship_ingestion_query(
        node_label_a, search_property_a, dict_key_a,
        node_label_b, search_property_b, dict_key_b,
        relationship_label, rel_property_map,
    )

    chunk = rel_mapping_list[:batch_size]
    cursor = 0
    while len(chunk) > 0:
        query_args = {
            'UpdateTag': update_tag,
            'RelMappingList': chunk,
        }
        try:
            tx.run(query, **query_args)
        except neo4j.ServiceUnavailable:
            logger.error("Failed to merge nodes.", exc_info=True)
            tx.rollback()
            raise
        cursor += batch_size
        chunk = rel_mapping_list[cursor:cursor + batch_size]

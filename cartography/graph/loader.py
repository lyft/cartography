from typing import List
from typing import Tuple
from typing import Dict
import logging

import neo4j

from cartography.graph.querybuilder import build_node_ingestion_query
from cartography.graph.querybuilder import build_relationship_ingestion_query

logger = logging.getLogger(__name__)


def merge_nodes_with_unwind(
    tx: neo4j.Transaction, node_label: str, id_value: str, field_list: List[Tuple[str, str]],
    node_data_list: List[Dict], update_tag: int, batch_size: int = 1000,
) -> None:
    if batch_size < 1:
        raise ValueError("batch_size cannot be less than 1.")

    ingest_query = build_node_ingestion_query(node_label, id_value, field_list)

    chunk = node_data_list[:batch_size]
    cursor = 0
    while len(chunk) > 0:
        query_args = {
            'UpdateTag': update_tag,
            'IdValue': id_value,
            'DictList': chunk,
        }
        try:
            tx.run(ingest_query, **query_args)
        except neo4j.ServiceUnavailable:
            logger.error("Failed to merge nodes.", exc_info=True)
            tx.rollback()
            raise
        cursor += batch_size
        chunk = node_data_list[cursor:cursor+batch_size]


def merge_relationships_with_unwind(
    tx: neo4j.Transaction, node_label_a: str, mapping_tuple_a: Tuple[str, str],
    node_label_b: str, mapping_tuple_b: Tuple[str, str], relationship_label_r: str,
    rel_data_list: List[Dict], update_tag: int, rel_field_list: List[Tuple[str, str]],
    batch_size: int = 1000,
)-> None:
    if batch_size < 1:
        raise ValueError("batch_size cannot be less than 1.")

    query = build_relationship_ingestion_query(
        node_label_a,
        mapping_tuple_a,
        node_label_b,
        mapping_tuple_b,
        relationship_label_r,
        rel_field_list,
    )

    chunk = rel_data_list[:batch_size]
    cursor = 0
    while len(chunk) > 0:
        query_args = {
            'UpdateTag': update_tag,
            'DictList': chunk,
        }
        try:
            tx.run(query, **query_args)
        except neo4j.ServiceUnavailable:
            logger.error("Failed to merge nodes.", exc_info=True)
            tx.rollback()
            raise
        cursor += batch_size
        chunk = rel_data_list[cursor:cursor+batch_size]

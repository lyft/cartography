from typing import List
from typing import Tuple
from typing import Dict
import logging

import neo4j

from cartography.graph.querybuilder import build_node_ingestion_query

logger = logging.getLogger(__name__)


def merge_nodes_with_unwind(
    tx: neo4j.Transaction, node_label: str, id_field: str, field_list: List[Tuple[str, str]],
    node_data_list: List[Dict], update_tag: int, batch_size: int = 1000,
) -> None:
    if batch_size < 1:
        raise ValueError("batch_size cannot be less than 1.")

    ingest_query = build_node_ingestion_query(node_label, id_field, field_list)

    chunk = node_data_list[:batch_size]
    cursor = 0
    while len(chunk) > 0:
        query_args = {
            'UpdateTag': update_tag,
            'IdField': id_field,
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
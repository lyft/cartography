import logging
from typing import Dict
from typing import List

import neo4j

from cartography.graph.querybuilder import build_node_ingestion_query
from cartography.graph.querybuilder import build_relationship_ingestion_query

logger = logging.getLogger(__name__)


def merge_nodes(
    tx: neo4j.Transaction, node_label: str, node_property_map: Dict[str, str],
    node_data_list: List[Dict], update_tag: int, batch_size: int = 1000,
) -> None:
    """
    Writes the `node_data_list` to Neo4j using the UNWIND + MERGE pattern in batches for performance
    and reliability. The query run looks like

    UNWIND {DictList} AS item
        MERGE (i:`node_label`{id:item.`node_property_map['id']`})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = {UpdateTag},
        ... <expand the given node property map to set the other node fields> ...

    If an error is encountered during this process, we rollback the transaction and raise the exception.
    :param tx: The Neo4j transaction
    :param node_label: The label of the node to MERGE to Neo4j
    :param node_property_map: Mapping from node field names to dict keys in `node_data_list`.
    :param node_data_list: A list of dicts to be written as nodes to the graph.
    :param update_tag: The cartography update tag.
    :param batch_size: Optional: the number of nodes to write in a single batch operation. Default = 1000.
    :return: None.
    """
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


def merge_relationships(
    tx: neo4j.Transaction, node_label_a: str, search_property_a: str, dict_key_a: str,
    node_label_b: str, search_property_b: str, dict_key_b: str,
    relationship_label: str,
    rel_mapping_list: List[Dict],
    update_tag: int,
    rel_property_map: Dict[str, str] = None,
    batch_size: int = 1000,
) -> None:
    """
    Writes relationships from nodes A to B using the `rel_mapping_list`. Employs the UNWIND + MERGE
    pattern in batches for performance and reliability. The query run looks like

    UNWIND {RelMappingList} AS item
        MATCH (a:`node_label_a`{`search_property_a`:item.`dict_key_a`})
        MATCH (b:`node_label_b`{`search_property_b`:item.`dict_key_b})
        MERGE (a)-[r:`rel_label`]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag},
            ... <optionally expands the relationship property map too> ...

    If an error is encountered during this process, we rollback the transaction and raise
    the exception.
    :param tx: The Neo4j transaction object.
    :param node_label_a: The label of node A.
    :param search_property_a: the search key to used to search the graph to find node A. For
    performance, this should be an indexed property. If your graph is large, querying on
    non-indexed properties can cause your syncs to take **days** to run!
    :param dict_key_a: The dict key on what value of `search_property_a` to search for.
    :param node_label_b: The label of node B.
    :param search_property_b: the search key to used to search the graph to find node B. For
    performance, this should be an indexed property. If your graph is large, querying on
    non-indexed properties can cause your syncs to take **days** to run!
    :param dict_key_b: The dict key on what value of `search_property_b` to search for.
    :param relationship_label: The $RELATIONSHIP_NAME from $NodeA to $NodeB.
    :param rel_mapping_list: List of relationship mappings. Has the shape
    [{'node_a_id': 123, 'node_b_id': 456, .. <opt rel attribs> ...}], which has the semantics
    "Draw a relationship from NodeA with id = 123 to NodeB with id = 456, adding any
    specified relationship attributes (if `rel_property_map` is provided)."
    :param update_tag: The update tag.
    :param rel_property_map: Optional mapping of relationship property names to set and their
    corresponding keys on the input data dict. Note: relationships in Neo4j 3.5 cannot be indexed
    so performing searches on them is slow. Reconsider your schema design if you expect to need
    to run queries using relationship fields as search keys.
    :param batch_size: Optional: the number of nodes to write in a single batch operation. Default = 1000.
    :return: None.
    """
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

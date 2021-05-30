from string import Template
from typing import Dict
from typing import List
from typing import Tuple
import logging

import neo4j

logger = logging.getLogger(__name__)


def build_node_ingestion_query(node_label: str, id_field: str, field_list: List[Tuple[str, str]]) -> str:
    """
    Generates Neo4j query string to write a list of dicts as nodes to the graph with the
    given node_label, id_field, and other arbitrary fields as provided by field_list. This
    uses the UNWIND + MERGE pattern to batch writes.
    The resulting `query` string can then be called with
    ```
    data_list: List[Dict] = {}
    neo4j_session.run(query, DictList=data_list, ...)
    ```

    :param node_label: The label of the node to create.
    :param id_field: The field on the node to designate as the unique identifier. Strongly
    recommend that `id` is used here.
    :param field_list: A list of 2-tuples of the form
           0: FieldName - the name of the field to set on the node
           1: FieldParamName - the dict key on where to access the value for this field.
    :return: A Neo4j query string using the UNWIND + MERGE pattern to write a list of nodes in batch.
    """
    ingest_preamble_template = Template("""
    UNWIND {DictList} AS item
        MERGE (i:$NodeLabel{$IdField:{IdValue}})
        ON CREATE SET i.firstseen = timestamp(),
        SET i.lastupdated = {UpdateTag}""")
    ingest_fields_template = Template('        i.$FieldName = item.$FieldParamName')

    ingest_preamble = ingest_preamble_template.safe_substitute(NodeLabel=node_label, IdField=id_field)
    if field_list:
        set_clause = ',\n'.join([
            ingest_fields_template.safe_substitute(FieldName=field_name, FieldParamName=field_param_name)
            for field_name, field_param_name in field_list
        ])
        ingest_query = ingest_preamble + ",\n" + set_clause
    else:
        ingest_query = ingest_preamble
    return ingest_query


def build_relationship_ingestion_query(
    label_a: str, mapping_tuple_a: Tuple[str, str], label_b: str, mapping_tuple_b: Tuple[str, str],
    label_r: str, rel_field_list: List[Tuple[str, str]],
) -> str:
    """
    Generates Neo4j query string to create the path `($NodeA)-[:$RELATIONSHIP_NAME]->($NodeB)`
    using an UNWIND + MERGE pattern. The resulting `query` string can then be called with
    ```
    data_list: List[Dict] = {}
    neo4j_session.run(query, DictList=data_list, ...)
    ```

    :param label_a: The label of $NodeA
    :param mapping_tuple_a: A tuple containing
            0. The field used to search for $NodeA in the graph (e.g. `id`)
            1. The dict key on where to access the value for this field (e.g. `item['Id']`)

            Explained another way, providing `('id', 'Id')` here tells cartography to
            set $NodeA.id with the value from `item['Id']`, where `item` is an item in
            `DictList`.
    :param label_b: The label of $NodeB.
    :param mapping_tuple_b: A tuple containing
            0. The field used to search for $NodeB in the graph (e.g. `id`)
            1. The dict key on where to access the value for this field (e.g. `item['Id']`)

            Explained another way, providing `('id', 'Id')` here tells cartography to
            set $NodeB.id with the value from `item['Id']`, where `item` is an item in
            `DictList`.
    :param label_r: The $RELATIONSHIP_NAME to merge between $NodeA and $NodeB.
    :param rel_field_list: Optional list of 2-tuples containing
            0. The field to add to the new relationship in the graph
            1. The dict key where on where to access the value for this field.
    :return: Generated Neo4j query string to draw relationships between all $NodeA and $NodeB
    in a given list.
    """
    ingest_preamble_template = Template("""
    UNWIND {DictList} AS item
        MATCH (a:$NodeLabelA{$SearchFieldA:item.$SearchParamA})
        MATCH (b:$NodeLabelB{$SearchFieldB:item.$SearchParamB})
        MERGE (a)-[r:$LabelR]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}""")
    ingest_fields_template = Template('        r.$FieldName = item.$FieldParamName')

    ingest_preamble = ingest_preamble_template.safe_substitute(
        NodeLabelA=label_a,
        SearchFieldA=mapping_tuple_a[0],
        SearchParamA=mapping_tuple_a[1],
        NodeLabelB=label_b,
        SearchFieldB=mapping_tuple_b[0],
        SearchParamB=mapping_tuple_b[1],
        LabelR=label_r,
    )
    if rel_field_list:
        set_clause = ',\n'.join([
            ingest_fields_template.safe_substitute(FieldName=field_name, FieldParamName=field_param_name)
            for field_name, field_param_name in rel_field_list
        ])
        ingest_query = ingest_preamble + ",\n" + set_clause
    else:
        ingest_query = ingest_preamble
    return ingest_query


def merge_nodes_with_unwind(
    tx: neo4j.Transaction, node_label: str, id_field: str, field_list: List[Tuple[str, str]],
    node_data_list: List[Dict], batch_size: int, update_tag: int,
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

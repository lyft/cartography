from typing import Dict
from typing import List
from typing import Tuple
from string import Template


import neo4j


def merge_nodes_with_unwind(
    neo4j_session: neo4j.Session, node_label: str, id_field: str, field_list: List[str], batch_size: int, tuple_list: List[Dict],
    update_tag: int,
) -> None:

    # TODO - consider having the transaction be about the entire load phase. all or nothing!
    # TODO - if there a spot that fails, then we shouldn't update the graph at all.
    tx: neo4j.Transaction = neo4j_session.write_transaction()

    ingest_query = build_node_ingestion_query(field_list, id_field, node_label)

    query_args = {
        'UpdateTag': update_tag,
        'IdField': id_field,
    }
    tx.run(ingest_query, **query_args)
    tx.commit()


def build_node_ingestion_query(node_label: str, id_field: str, field_list: List[Tuple[str, str]]) -> str:
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
    label_a: str, id_tuple_a: Tuple[str, str], label_b: str, id_tuple_b: Tuple[str, str], label_r: str,
    rel_field_list: List,
) -> str:
    ingest_preamble_template = Template("""
    UNWIND {DictList} AS item
        MATCH (a:$NodeLabelA{$IdFieldA:item.$IdParamA})
        MATCH (b:$NodeLabelB{$IdFieldB:item.$IdParamB})
        MERGE (a)-[r:$LabelR]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}""")
    ingest_fields_template = Template('        r.$FieldName = r.$FieldParamName')

    ingest_preamble = ingest_preamble_template.safe_substitute(
        NodeLabelA=label_a,
        IdFieldA=id_tuple_a[0],
        IdParamA=id_tuple_a[1],
        NodeLabelB=label_b,
        IdFieldB=id_tuple_b[0],
        IdParamB=id_tuple_b[1],
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

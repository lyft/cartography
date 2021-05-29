from string import Template
from typing import List
from typing import Tuple


def build_node_ingestion_query(node_label: str, id_field: str, field_list: List[Tuple[str, str]]) -> str:
    """
    Generates query to write a list of dicts as nodes to the graph with the given node_label,
    id_field, and other arbitrary fields as provided by field_list.
    The generated query includes a hardcoded {DictList} parameter that the caller
    can use to pass in a list of dicts to the query.
    :param node_label: The label of the node to create.
    :param id_field: The field on the node to designate as the unique identifier. Strongly
    recommend that `id` is used here.
    :param field_list: A list of 2-tuples of the form
           0: FieldName - the name of the field to set on the node
           1: FieldParamName - the dict key on where to access the value for this field.
    :return:
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
    label_a: str, id_tuple_a: Tuple[str, str], label_b: str, id_tuple_b: Tuple[str, str], label_r: str,
    rel_field_list: List,
) -> str:
    """
    Generates query to create the path ($NodeA)-[:$RELATIONSHIP_NAME]->($NodeB).
    The generated query includes a hardcoded {DictList} parameter that the caller
    can use to pass in a list of dicts to the query.
    Precondition: Both nodes A and B must already exist in the graph.
    :param label_a: The label of $NodeA
    :param id_tuple_a: A tuple containing
            0. The node field used to uniquely identify $NodeA in the graph.
            1. The dict key on where to access the value for this field.
    :param label_b: The label of $NodeB.
    :param id_tuple_b: A tuple containing
            0. The node field used to uniquely identify $NodeB in the graph.
            1. The dict key on where to access the value for this field.
    :param label_r: The $RELATIONSHIP_NAME to merge between $NodeA and $NodeB.
    :param rel_field_list: Optional list of 2-tuples containing
            0. The field to add to the new relationship in the graph
            1. The dict key where on where to access the value for this field.
    :return: Generated Neo4j query string to draw a relationship between $NodeA and $NodeB.
    """
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

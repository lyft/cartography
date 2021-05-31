from string import Template
from typing import Dict


def build_node_ingestion_query(node_label: str, node_property_map: Dict[str, str]) -> str:
    """
    Generates Neo4j query string to write a list of dicts as nodes to the graph with the
    given node_label, id_field, and other arbitrary fields as provided by field_list. This
    uses the UNWIND + MERGE pattern to batch writes.

    :param node_label: The label of the nodes to write, e.g. EC2Instance
    :param node_property_map: A mapping of node property names to dict key names.
    :return: A Neo4j query string using the UNWIND + MERGE pattern to write a list of nodes
    in batch. This exposes 2 parameters: `{DictList}` accepts a list of dictionaries to
    write as nodes to the graph, and `{UpdateTag}` is the standard cartography int update tag.
    """
    if 'id' not in node_property_map or not node_property_map['id']:
        raise ValueError('node_property_map must have key `id` set.')

    ingest_preamble_template = Template("""
    UNWIND {DictList} AS item
        MERGE (i:$NodeLabel{id:item.$DictIdField})
        ON CREATE SET i.firstseen = timestamp()
        SET i.lastupdated = {UpdateTag}""")
    ingest_fields_template = Template('        i.$NodeProperty = item.$DictProperty')

    ingest_preamble = ingest_preamble_template.safe_substitute(
        NodeLabel=node_label, DictIdField=node_property_map['id'],
    )

    # If the node_property_map contains more than just `id`, generate a SET statement for the other fields.
    if len(node_property_map.keys()) > 1:
        set_clause = ',\n'.join([
            ingest_fields_template.safe_substitute(NodeProperty=node_property, DictProperty=dict_property)
            for node_property, dict_property in node_property_map.items()
            if not node_property == 'id'  # Make sure to exclude setting the `id` again.
        ])
        ingest_query = ingest_preamble + ",\n" + set_clause
    else:
        ingest_query = ingest_preamble
    return ingest_query


def build_relationship_ingestion_query(
    node_label_a: str, search_property_a: str, dict_key_a: str,
    node_label_b: str, search_property_b: str, dict_key_b: str,
    rel_label: str,
    rel_property_map: Dict[str, str] = None,
) -> str:
    """
    Generates Neo4j query string to search the graph for nodes A and B using the given
    `node_property_map` and draw a relationship between them. The resulting path is
    `($NodeA)-[:$RELATIONSHIP_NAME]->($NodeB)`. The caller can also optionally provide a
    `rel_property_map` to define properties for the new relationship - see notes below on what
    this means for performance.

    The resulting `query` string uses an UNWIND + MERGE pattern so that relationships are
    created in batches. The returned query can then be called with

    ```
    data_list: List[Dict] = {}
    neo4j_session.run(query, DictList=data_list, ...)
    ```

    :param node_label_a: The label of $NodeA.
    :param search_property_a: the search key to used to search the graph to find node A. For
    performance, this should be an indexed property. If your graph is large, querying on
    non-indexed properties can cause your syncs to take **days** to run!
    :param dict_key_a: The dict key on what value of `search_property_a` to search for.
    :param node_label_b: The label of $NodeB.
    :param search_property_b: the search key to used to search the graph to find node B. For
    performance, this should be an indexed property. If your graph is large, querying on
    non-indexed properties can cause your syncs to take **days** to run!
    :param dict_key_b: The dict key on what value of `search_property_b` to search for.
    :param rel_label: The $RELATIONSHIP_NAME from $NodeA to $NodeB.
    :param rel_property_map: Optional mapping of relationship property names to set and their
    corresponding keys on the input data dict. Note: relationships in Neo4j 3.5 cannot be indexed
    so performing searches on them is slow. Reconsider your schema design if you expect to need
    to run queries using relationship fields as search keys.
    :return: Neo4j query string to draw relationships between $NodeA and $NodeB. This exposes 2
    parameters: `{DictList}` accepts a list of dictionaries to write as relationships to the
    graph, and `{UpdateTag}` is the standard cartography int update tag.
    """
    ingest_preamble_template = Template("""
    UNWIND {DictList} AS item
        MATCH (a:$NodeLabelA{$SearchPropertyA:item.$DictKeyA})
        MATCH (b:$NodeLabelB{$SearchPropertyB:item.$DictKeyB})
        MERGE (a)-[r:$LabelR]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {UpdateTag}""")
    ingest_fields_template = Template('        r.$RelProperty = item.$DictProperty')

    ingest_preamble = ingest_preamble_template.safe_substitute(
        NodeLabelA=node_label_a,
        SearchPropertyA=search_property_a,
        DictKeyA=dict_key_a,
        NodeLabelB=node_label_b,
        SearchPropertyB=search_property_b,
        DictKeyB=dict_key_b,
        LabelR=rel_label,
    )

    if rel_property_map:
        set_clause = ',\n'.join([
            ingest_fields_template.safe_substitute(RelProperty=rel_property, DictProperty=dict_property)
            for rel_property, dict_property in rel_property_map.items()
        ])
        ingest_query = ingest_preamble + ",\n" + set_clause
    else:
        ingest_query = ingest_preamble
    return ingest_query

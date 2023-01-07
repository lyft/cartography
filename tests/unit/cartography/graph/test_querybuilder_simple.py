from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeWithSubResourceSchema
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


def test_simplenode_sanity_checks():
    """
    Test creating a simple node schema with no relationships.
    """
    schema: SimpleNodeSchema = SimpleNodeSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_node_labels is None
    assert schema.sub_resource_relationship is None
    assert schema.other_relationships is None


def test_simplenode_with_subresource_sanity_checks():
    """
    Test creating a simple node schema with no relationships and ensure that the optional attributes are indeed None.
    """
    schema: SimpleNodeWithSubResourceSchema = SimpleNodeWithSubResourceSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_node_labels is None
    assert schema.other_relationships is None


def test_build_ingestion_query_with_sub_resource():
    """
    Test creating a simple node schema with a sub resource relationship.
    """
    # Act
    query = build_ingestion_query(SimpleNodeWithSubResourceSchema())

    expected = """
        UNWIND $DictList AS item
            MERGE (i:SimpleNode{id: item.Id})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.property1 = item.property1,
                i.property2 = item.property2

            WITH i, item
            CALL {
                WITH i, item
                OPTIONAL MATCH (j:SubResource{id: $sub_resource_id})
                WITH i, item, j WHERE j IS NOT NULL
                MERGE (i)<-[r:RELATIONSHIP_LABEL]-(j)
                ON CREATE SET r.firstseen = timestamp()
                SET
                    r.lastupdated = $lastupdated
            }
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query

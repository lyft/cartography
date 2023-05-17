from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.fake_emps_githubusers import FakeEmpSchema
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
# TODO - figure out wtf I want to do here with this id field COALESCING :\
    expected = """
        UNWIND $DictList AS item
            MERGE (i:SimpleNode{id: item.Id})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.property1 = COALESCE(item.property1, i.property1),
                i.property2 = COALESCE(item.property2, i.property2)

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


def test_build_ingestion_query_case_insensitive_match():
    query = build_ingestion_query(FakeEmpSchema())

    expected = """
        UNWIND $DictList AS item
            MERGE (i:FakeEmployee{id: item.id})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.email = COALESCE(item.email, i.email),
                i.github_username = COALESCE(item.github_username, i.github_username)

            WITH i, item
            CALL {
                WITH i, item
                OPTIONAL MATCH (n0:GitHubUser)
                WHERE
                    toLower(n0.username) = toLower(item.github_username)
                WITH i, item, n0 WHERE n0 IS NOT NULL
                MERGE (i)-[r0:IDENTITY_GITHUB]->(n0)
                ON CREATE SET r0.firstseen = timestamp()
                SET
                    r0.lastupdated = $lastupdated
            }
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query

from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


def test_build_ingestion_query_complex():
    # Act
    query = build_ingestion_query(InterestingAssetSchema())

    expected = """
        UNWIND $DictList AS item
            MERGE (i:InterestingAsset{id: COALESCE(item.Id, i.id)})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.property1 = COALESCE(item.property1, i.property1),
                i.property2 = COALESCE(item.property2, i.property2),
                i:AnotherNodeLabel:YetAnotherNodeLabel

            WITH i, item
            CALL {
                WITH i, item
                OPTIONAL MATCH (j:SubResource{id: $sub_resource_id})
                WITH i, item, j WHERE j IS NOT NULL
                MERGE (i)<-[r:RELATIONSHIP_LABEL]-(j)
                ON CREATE SET r.firstseen = timestamp()
                SET
                    r.lastupdated = $lastupdated,
                    r.another_rel_field = COALESCE(item.AnotherField, i.anotherfield),
                    r.yet_another_rel_field = COALESCE(item.YetAnotherRelField, i.yetanotherrelfield)

                UNION
                WITH i, item
                OPTIONAL MATCH (n0:HelloAsset)
                WHERE
                    n0.id = COALESCE(item.hello_asset_id, i.hello_asset_id)
                WITH i, item, n0 WHERE n0 IS NOT NULL
                MERGE (i)-[r0:ASSOCIATED_WITH]->(n0)
                ON CREATE SET r0.firstseen = timestamp()
                SET
                    r0.lastupdated = $lastupdated

                UNION
                WITH i, item
                OPTIONAL MATCH (n1:WorldAsset)
                WHERE
                    n1.id = COALESCE(item.world_asset_id, i.world_asset_id)
                WITH i, item, n1 WHERE n1 IS NOT NULL
                MERGE (i)<-[r1:CONNECTED]-(n1)
                ON CREATE SET r1.firstseen = timestamp()
                SET
                    r1.lastupdated = $lastupdated
            }
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query

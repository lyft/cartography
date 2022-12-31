from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import MERGE_SUB_RESOURCE_QUERY, \
    MERGE_HELLO_ASSET_QUERY, MERGE_WORLD_ASSET_QUERY, INTERESTING_NODE_WITH_ALL_RELS
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema, \
    InterestingAssetToWorldAssetRel


def test_cleanup_simplenode(neo4j_session):
    # Arrange: add (:SubResource{id:sub-resource-id}) and (:WorldAsset{id: world-asset-id}) to the test graph,
    neo4j_session.run(MERGE_SUB_RESOURCE_QUERY)
    neo4j_session.run(MERGE_HELLO_ASSET_QUERY)
    neo4j_session.run(MERGE_WORLD_ASSET_QUERY)

    query = build_ingestion_query(InterestingAssetSchema())
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_WITH_ALL_RELS,
        lastupdated=1,
        sub_resource_id='sub-resource-id',
    )
    # Verify that everything exists as expected
    expected = {('interesting-node-id', 'the-worldasset-id-1')}
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:CONNECTED]-(n2:WorldAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r['n1.id'], r['n2.id']) for r in result}
    assert actual == expected

    # Act: Generate and run the cleanup job
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {'UPDATE_TAG': 2, 'sub_resource_id': 'sub-resource-id'},
    )
    cleanup_job.run(neo4j_session)

    # Assert that everything has been cleaned up
    expected = set()
    result = neo4j_session.run(
        """
        MATCH (n1:InterestingAsset)<-[:CONNECTED]-(n2:WorldAsset) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r['n1.id'], r['n2.id']) for r in result}
    assert actual == expected

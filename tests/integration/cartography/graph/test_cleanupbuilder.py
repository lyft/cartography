from cartography.client.core.tx import load_graph_data
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import INTERESTING_NODE_SUB_RES_ONLY
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import INTERESTING_NODE_WITH_ALL_RELS
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import MERGE_HELLO_ASSET_QUERY
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import MERGE_SUB_RESOURCE_QUERY
from tests.data.graph.querybuilder.sample_data.helloworld_relationships import MERGE_WORLD_ASSET_QUERY
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.integration.util import check_rels


def test_cleanup_interesting_asset_end_to_end(neo4j_session):
    # Arrange: add (:SubResource{id:sub-resource-id}), (:HelloAsset{id: the-helloasset-id-1}),
    # (:WorldAsset{id: world-asset-id}) to the test graph.
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
    # Sanity checks to verify that the relationships exist.
    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'WorldAsset',
        'id',
        'CONNECTED',
        rel_direction_left=True,
    ) == {('interesting-node-id', 'the-worldasset-id-1')}

    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'HelloAsset',
        'id',
        'ASSOCIATED_WITH',
        rel_direction_left=False,
    ) == {('interesting-node-id', 'the-helloasset-id-1')}

    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'SubResource',
        'id',
        'RELATIONSHIP_LABEL',
        rel_direction_left=True,
    ) == {('interesting-node-id', 'sub-resource-id')}

    # Arrange: Suppose only InterestingAsset and its SubResource connection exist now.
    load_graph_data(
        neo4j_session,
        query,
        INTERESTING_NODE_SUB_RES_ONLY,
        lastupdated=2,
        sub_resource_id='sub-resource-id',
    )

    # Act: Now actually generate and run the cleanup job.
    cleanup_job = GraphJob.from_node_schema(
        InterestingAssetSchema(),
        {'UPDATE_TAG': 2, 'sub_resource_id': 'sub-resource-id'},
    )
    cleanup_job.run(neo4j_session)

    # Assert that everything has been cleaned up, EXCEPT for InterestingAsset and its SubResource.
    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'WorldAsset',
        'id',
        'CONNECTED',
        rel_direction_left=True,
    ) == set()

    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'HelloAsset',
        'id',
        'ASSOCIATED_WITH',
        rel_direction_left=False,
    ) == set()

    # This is the only one we expect to remain intact.
    assert check_rels(
        neo4j_session,
        'InterestingAsset',
        'id',
        'SubResource',
        'id',
        'RELATIONSHIP_LABEL',
        rel_direction_left=True,
    ) == {('interesting-node-id', 'sub-resource-id')}

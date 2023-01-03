from cartography.graph.cleanupbuilder import _build_cleanup_node_query
from cartography.graph.cleanupbuilder import _build_cleanup_rel_query
from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.job import get_parameters
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetToHelloAssetRel
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


def test_cleanup_node_sub_rel_only():
    """
    Test that we correctly generate a query to delete stale nodes that are attached to a sub resource.
    """
    actual_query: str = _build_cleanup_node_query(InterestingAssetSchema())
    expected_query = """
        MATCH (n:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected_query)


def test_cleanup_node_with_selected_rel():
    """
    Test that we correctly generate a query to delete stale nodes that are attached to a sub resource and to one other
    node type.
    """
    actual_query: str = _build_cleanup_node_query(InterestingAssetSchema(), InterestingAssetToHelloAssetRel())
    expected = """
        MATCH (n:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (n)-[:ASSOCIATED_WITH]->(:HelloAsset)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected)


def test_cleanup_rel_sub_rel_only():
    """
    Test that we correctly generate a query to delete stale relationships between a target node (HelloAsset in this
    case) its sub resource (SubResource in this case).
    """
    actual_query: str = _build_cleanup_rel_query(InterestingAssetSchema())
    expected_query = """
        MATCH (:InterestingAsset)<-[r:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected_query)


def test_cleanup_rel_with_selected_rel():
    """
    Test that we correctly generate a query to delete stale relationships between 2 target nodes (InterestingAsset and
    HelloAsset in this test case) where the main target node is bound to a sub resource.
    """
    actual_query: str = _build_cleanup_rel_query(
        InterestingAssetSchema(),
        InterestingAssetToHelloAssetRel(),
    )
    expected_query = """
        MATCH (src:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (src)-[r:ASSOCIATED_WITH]->(:HelloAsset)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected_query)


def test_get_params_from_queries():
    """
    Test that we are able to correctly retrieve parameter names from the generated cleanup queries.
    """
    queries: list[str] = build_cleanup_queries(InterestingAssetSchema())
    assert set(get_parameters(queries)) == {'UPDATE_TAG', 'sub_resource_id', 'LIMIT_SIZE'}


# TODO test exceptions

import pytest

from cartography.graph.cleanupbuilder import _build_cleanup_node_query
from cartography.graph.cleanupbuilder import _build_cleanup_rel_query
from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.job import get_parameters
from cartography.intel.aws.emr import EMRClusterToAWSAccount
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetToHelloAssetRel
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetToSubResourceRel
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema
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


def test_cleanup_node_sub_rel_only_no_sub_res_raises_exc():
    """
    Test that we raise a ValueError when building cleanup query for node_schema without a sub resource relationship.
    """
    with pytest.raises(ValueError):
        _build_cleanup_node_query(SimpleNodeSchema())


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


def test_cleanup_node_with_invalid_selected_rel_raises_exc():
    """
    Test that we raise a ValueError if we try to cleanup a node and provide a specified rel but the rel doesn't exist on
    the node schema.
    """
    with pytest.raises(ValueError):
        _build_cleanup_node_query(InterestingAssetSchema(), EMRClusterToAWSAccount())


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


def test_cleanup_rel_sub_rel_only_no_sub_resource_raises_exc():
    """
    Test that _build_cleanup_rel_query() raises a ValueError when trying to generate a query for a node_schema without a
    sub resource relationship.
    """
    with pytest.raises(ValueError):
        _build_cleanup_rel_query(SimpleNodeSchema())


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


def test_cleanup_rel_with_selected_rel_that_does_not_exist_raises_exc():
    """
    Test we raise a ValueError when a selected rel is specified that does not exist to _build_cleanup_rel_query.
    """
    with pytest.raises(ValueError):
        _build_cleanup_rel_query(
            InterestingAssetSchema(),
            EMRClusterToAWSAccount(),
        )


def test_get_params_from_queries():
    """
    Test that we are able to correctly retrieve parameter names from the generated cleanup queries.
    """
    queries: list[str] = build_cleanup_queries(InterestingAssetSchema())
    assert set(get_parameters(queries)) == {'UPDATE_TAG', 'sub_resource_id', 'LIMIT_SIZE'}


def test_get_build_cleanup_queries_selected_rels():
    """
    Test that we are able to correctly make cleanup jobs for a subset of relationships.
    """
    queries: list[str] = build_cleanup_queries(
        InterestingAssetSchema(),
        {InterestingAssetToSubResourceRel(), InterestingAssetToHelloAssetRel()},
    )
    assert len(queries) == 4  # == 2 to delete nodes and rels bound to the sub resource + 2 for the HelloAsset


def test_get_build_cleanup_queries_selected_rels_no_sub_res_raises_exc():
    """
    Test that not specifying the sub resource rel raises an exception
    """
    with pytest.raises(ValueError):
        build_cleanup_queries(
            InterestingAssetSchema(),
            {InterestingAssetToHelloAssetRel()},
        )

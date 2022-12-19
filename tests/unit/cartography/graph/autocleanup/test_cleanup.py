from cartography.graph.cleanupbuilder import build_cleanup_node_query
from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.cleanupbuilder import build_cleanup_rel_query
from cartography.graph.job import get_parameters
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetToHelloAssetRel
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


def test_cleanup_node():
    actual_query: str = build_cleanup_node_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
        InterestingAssetToHelloAssetRel(),
    )
    expected = """
        MATCH (src:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        MATCH (src)-[:ASSOCIATED_WITH]->(n:HelloAsset)
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected)


def test_cleanup_node_sub_rel_only():
    actual_query: str = build_cleanup_node_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
    )
    expected_query = """
        MATCH (n:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE n.lastupdated <> $UPDATE_TAG
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected_query)


def test_cleanup_rel():
    actual_query: str = build_cleanup_rel_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
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


def test_cleanup_rel_sub_rel_only():
    actual_query: str = build_cleanup_rel_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
    )
    expected_query = """
        MATCH (:InterestingAsset)<-[r:RELATIONSHIP_LABEL]-(:SubResource{id: $sub_resource_id})
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
    """
    assert remove_leading_whitespace_and_empty_lines(actual_query) == \
        remove_leading_whitespace_and_empty_lines(expected_query)


def test_cleanup_node_queries():
    queries: list[str] = build_cleanup_queries(InterestingAssetSchema())
    from pprint import pprint
    pprint(queries)


def test_get_params():
    query = "this is the $variable and another $one"
    query2 = "$var = 1, $var2 = 3"
    params = get_parameters([query, query2])
    print(params)


def test_get_params_from_queries():
    queries: list[str] = build_cleanup_queries(InterestingAssetSchema())
    params = get_parameters(queries)
    print(params)

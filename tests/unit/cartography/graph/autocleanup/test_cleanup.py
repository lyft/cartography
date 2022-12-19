from cartography.graph.cleanupbuilder import build_cleanup_node_query
from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.cleanupbuilder import build_cleanup_rel_query
from cartography.graph.job import get_parameters
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import make_target_node_matcher
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetToHelloAssetRel


def test_cleanup_node():
    cleanup_query: str = build_cleanup_node_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
        InterestingAssetToHelloAssetRel(),
    )
    print(cleanup_query)


def test_cleanup_node_sub_rel_only():
    cleanup_query: str = build_cleanup_node_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
    )
    print(cleanup_query)


def test_cleanup_rel():
    cleanup_query: str = build_cleanup_rel_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
        InterestingAssetToHelloAssetRel(),
    )
    print(cleanup_query)


def test_cleanup_rel_sub_rel_only():
    cleanup_query: str = build_cleanup_rel_query(
        InterestingAssetSchema(),
        make_target_node_matcher({'id': PropertyRef('sub_resource_id', set_in_kwargs=True)}),
    )
    print(cleanup_query)
    from string import Formatter
    print(list(Formatter().parse(cleanup_query)))


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

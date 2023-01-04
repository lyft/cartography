from cartography.graph.querybuilder import build_create_index_queries
from cartography.intel.aws.emr import EMRClusterSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import InterestingAssetSchema


def test_build_create_index_queries():
    result = build_create_index_queries(InterestingAssetSchema())
    assert result


def test_build_create_index_queries():
    result = build_create_index_queries(EMRClusterSchema())
    assert result

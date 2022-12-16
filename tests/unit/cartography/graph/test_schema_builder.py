from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.schema_builder import build_node_properties
from cartography.graph.schema_builder import build_node_schema
from cartography.graph.schema_builder import build_rel_properties
from cartography.graph.schema_builder import build_rel_schema
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeWithSubResourceSchema
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


def test_build_node_schema_simple():
    '''
    Test that our build_node_schema() function can produce an identical schema and query to
     schemas for which we manually build the classes.
    '''
    original_schema: SimpleNodeWithSubResourceSchema = SimpleNodeWithSubResourceSchema()

    built_schema: CartographyNodeSchema = build_node_schema(
        cls_name='SimpleNodeWithSubResourceSchema',
        label='SimpleNode',
        properties=build_node_properties(
            'SimpleNodeProperties',
            id=PropertyRef('Id'),
            lastupdated=PropertyRef('lastupdated', set_in_kwargs=True),
            property1=PropertyRef('property1'),
            property2=PropertyRef('property2'),
        ),
        sub_resource_relationship=build_rel_schema(
            cls_name='SimpleNodeToSubResourceRel',
            target_node_label='SubResource',
            target_node_matcher=make_target_node_matcher(
                dict(id=PropertyRef('sub_resource_id', set_in_kwargs=True)),
            ),
            direction=LinkDirection.INWARD,
            rel_label='RELATIONSHIP_LABEL',
            properties=build_rel_properties(
                cls_name='SimpleNodeToSubResourceRelProps',
                lastupdated=PropertyRef('lastupdated', set_in_kwargs=True),
            ),
        ),
    )

    expected_query = build_ingestion_query(original_schema)
    actual_query = build_ingestion_query(built_schema)

    expected_query = remove_leading_whitespace_and_empty_lines(expected_query)
    actual_query = remove_leading_whitespace_and_empty_lines(actual_query)
    assert expected_query == actual_query

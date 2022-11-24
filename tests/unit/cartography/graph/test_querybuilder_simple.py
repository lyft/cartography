"""
Test cases

- Single node label
- Multiple node labels
- Node properties x
- Relationship properties x
- Additional links
"""
from dataclasses import dataclass

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import build_ingestion_query
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines


@dataclass
class SimpleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)
    property1: PropertyRef = PropertyRef('property1')
    property2: PropertyRef = PropertyRef('property2')


@dataclass
class SimpleNodeToSubResourceRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)


@dataclass
class SimpleNodeToSubResourceRel(CartographyRelSchema):
    """
    Define a sub resource rel:
    (:EMRCluster)<-[:RESOURCE]-(:AWSAccount)
    """
    target_node_label: str = 'SubResource'
    target_node_key: str = 'id'
    target_node_key_property_ref: PropertyRef = PropertyRef('sub_resource_id', static=True)
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RELATIONSHIP_LABEL"
    properties: SimpleNodeToSubResourceRelProps = SimpleNodeToSubResourceRelProps()


@dataclass
class SimpleNodeSchema(CartographyNodeSchema):
    label: str = 'SimpleNode'
    properties: SimpleNodeProperties = SimpleNodeProperties()


@dataclass
class SimpleNodeWithSubResourceSchema(CartographyNodeSchema):
    """
    Same as SimpleNodeSchema but with a sub-resource relationship now.
    """
    label: str = 'SimpleNode'
    properties: SimpleNodeProperties = SimpleNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SimpleNodeToSubResourceRel()


def test_simplenode_sanity_checks():
    """
    Test creating a simple node schema with no relationships
    """
    schema: SimpleNodeSchema = SimpleNodeSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_labels is None
    assert schema.sub_resource_relationship is None
    assert schema.other_relationships is None


def test_simplenode_with_subresource_sanity_checks():
    """
    Test creating a simple node schema with a subresource relationship
    """
    schema: SimpleNodeWithSubResourceSchema = SimpleNodeWithSubResourceSchema()
    # Assert that the unimplemented, non-abstract properties have None values.
    assert schema.extra_labels is None
    assert schema.other_relationships is None


def test_build_ingestion_query_with_subresource():
    # Act
    query = build_ingestion_query(SimpleNodeWithSubResourceSchema())

    expected = """
        UNWIND $DictList AS item
            MERGE (i:SimpleNode{id: item.Id})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.property1 = item.property1,
                i.property2 = item.property2

            WITH i, item
            MATCH (j:SubResource{id: $sub_resource_id})
            MERGE (i)<-[r:RELATIONSHIP_LABEL]-(j)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r.lastupdated = $lastupdated
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query

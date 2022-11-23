from dataclasses import dataclass
from typing import List
from typing import Optional

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.querybuilder import build_ingestion_query
from cartography.graph.querybuilder import default_field
from tests.unit.cartography.graph.helpers import remove_leading_whitespace_and_empty_lines
from tests.unit.cartography.graph.test_querybuilder_simple import SimpleNodeProperties


@dataclass
class InterestingAssetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)
    property1: PropertyRef = PropertyRef('property1')
    property2: PropertyRef = PropertyRef('property2')


@dataclass
class InterestingAssetToSubResourceRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)
    another_rel_field: PropertyRef = PropertyRef('AnotherField')
    yet_another_rel_field: PropertyRef = PropertyRef("YetAnotherRelField")


# (:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource)
@dataclass
class InterestingAssetToSubResourceRel(CartographyRelSchema):
    target_node_label: str = 'SubResource'
    target_node_key: str = 'id'
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RELATIONSHIP_LABEL"
    properties: InterestingAssetToSubResourceRelProps = InterestingAssetToSubResourceRelProps()
    dict_field_ref: PropertyRef = PropertyRef('subresource_id', static=True)


@dataclass
class InterestingAssetToHelloAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)


# (:InterestingAsset)-[:ASSOCIATED_WITH]->(:HelloAsset)
@dataclass
class InterestingAssetToHelloAssetRel(CartographyRelSchema):
    target_node_label: str = 'HelloAsset'
    target_node_key: str = 'id'
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: InterestingAssetToHelloAssetRelProps = InterestingAssetToHelloAssetRelProps()
    dict_field_ref: PropertyRef = PropertyRef('hello_asset_id')


@dataclass
class InterestingAssetToWorldAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', static=True)


# (:InterestingAsset)<-[:CONNECTED]-(:WorldAsset)
@dataclass
class InterestingAssetToWorldAssetRel(CartographyRelSchema):
    target_node_label: str = 'WorldAsset'
    target_node_key: str = 'id'
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED"
    properties: InterestingAssetToWorldAssetRelProps = InterestingAssetToWorldAssetRelProps()
    dict_field_ref: PropertyRef = PropertyRef('world_asset_id')


@dataclass
class InterestingAssetSchema(CartographyNodeSchema):
    extra_labels: Optional[List[str]] = default_field(['AnotherNodeLabel', 'YetAnotherNodeLabel'])
    label: str = 'InterestingNode'
    properties: SimpleNodeProperties = SimpleNodeProperties()
    subresource_relationship: InterestingAssetToSubResourceRel = InterestingAssetToSubResourceRel()
    other_relationships: Optional[List[CartographyRelSchema]] = default_field(
        [
            InterestingAssetToHelloAssetRel(),
            InterestingAssetToWorldAssetRel(),
        ],
    )


def test_build_ingestion_query_complex():
    # Act
    query = build_ingestion_query(InterestingAssetSchema())

    expected = """
        UNWIND $DictList AS item
            MERGE (i:InterestingNode{id: item.Id})
            ON CREATE SET i.firstseen = timestamp()
            SET
                i.lastupdated = $lastupdated,
                i.property1 = item.property1,
                i.property2 = item.property2,
                i:AnotherNodeLabel:YetAnotherNodeLabel

            WITH i, item
            MATCH (j:SubResource{id: $subresource_id})
            MERGE (i)<-[r:RELATIONSHIP_LABEL]-(j)
            ON CREATE SET r.firstseen = timestamp()
            SET
                r.lastupdated = $lastupdated,
                r.another_rel_field = item.AnotherField,
                r.yet_another_rel_field = item.YetAnotherRelField

            WITH i, item
            MATCH (n0:HelloAsset{id: item.hello_asset_id})
            MERGE (i)-[r0:ASSOCIATED_WITH]->(n0)
            ON CREATE SET r0.firstseen = timestamp()
            SET
                r0.lastupdated = $lastupdated

            WITH i, item
            MATCH (n1:WorldAsset{id: item.world_asset_id})
            MERGE (i)<-[r1:CONNECTED]-(n1)
            ON CREATE SET r1.firstseen = timestamp()
            SET
                r1.lastupdated = $lastupdated
    """

    # Assert: compare query outputs while ignoring leading whitespace.
    actual_query = remove_leading_whitespace_and_empty_lines(query)
    expected_query = remove_leading_whitespace_and_empty_lines(expected)
    assert actual_query == expected_query

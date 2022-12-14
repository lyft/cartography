from dataclasses import dataclass
from typing import List
from typing import Optional

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from cartography.graph.querybuilder import default_field
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeProperties


@dataclass
class InterestingAssetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    property1: PropertyRef = PropertyRef('property1')
    property2: PropertyRef = PropertyRef('property2')


@dataclass
class InterestingAssetToSubResourceRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    another_rel_field: PropertyRef = PropertyRef('AnotherField')
    yet_another_rel_field: PropertyRef = PropertyRef("YetAnotherRelField")


@dataclass
class InterestingAssetToSubResourceRel(CartographyRelSchema):
    """
    Define a sub resource relationship
    (:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource)
    """
    target_node_label: str = 'SubResource'
    target_node_matcher: TargetNodeMatcher = TargetNodeMatcher(
        {'id': PropertyRef('sub_resource_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RELATIONSHIP_LABEL"
    properties: InterestingAssetToSubResourceRelProps = InterestingAssetToSubResourceRelProps()


@dataclass
class InterestingAssetToHelloAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass
class InterestingAssetToHelloAssetRel(CartographyRelSchema):
    """
    Define an additional relationship
    (:InterestingAsset)-[:ASSOCIATED_WITH]->(:HelloAsset)
    """
    target_node_label: str = 'HelloAsset'
    target_node_matcher: TargetNodeMatcher = TargetNodeMatcher({'id': PropertyRef('hello_asset_id')})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: InterestingAssetToHelloAssetRelProps = InterestingAssetToHelloAssetRelProps()


@dataclass
class InterestingAssetToWorldAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass
class InterestingAssetToWorldAssetRel(CartographyRelSchema):
    """
    Define yet another relationship.
    (:InterestingAsset)<-[:CONNECTED]-(:WorldAsset)
    """
    target_node_label: str = 'WorldAsset'
    target_node_matcher: TargetNodeMatcher = TargetNodeMatcher({'id': PropertyRef('world_asset_id')})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED"
    properties: InterestingAssetToWorldAssetRelProps = InterestingAssetToWorldAssetRelProps()


@dataclass
class InterestingAssetSchema(CartographyNodeSchema):
    extra_labels: Optional[List[str]] = default_field(['AnotherNodeLabel', 'YetAnotherNodeLabel'])
    label: str = 'InterestingAsset'
    properties: SimpleNodeProperties = SimpleNodeProperties()
    sub_resource_relationship: InterestingAssetToSubResourceRel = InterestingAssetToSubResourceRel()
    other_relationships: Optional[List[CartographyRelSchema]] = default_field(
        [
            InterestingAssetToHelloAssetRel(),
            InterestingAssetToWorldAssetRel(),
        ],
    )

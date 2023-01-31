from dataclasses import dataclass

from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import make_target_node_matcher
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeProperties


@dataclass(frozen=True)
class FakeEC2InstanceToAWSAccountRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class FakeEC2InstanceToAWSAccount(CartographyRelSchema):
    """
    The PropertyRef is intentionally set to False: we expect the unit test to raise an exception.
    Auto cleanups require the sub resource target node matcher to have set_in_kwargs=True because of how the GraphJob
    class does query parameterization.
    """
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=False)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FakeEC2InstanceToAWSAccountRelProps = FakeEC2InstanceToAWSAccountRelProps()


@dataclass(frozen=True)
class FakeEC2InstanceSchema(CartographyNodeSchema):
    label: str = 'FakeEC2Instance'
    properties: SimpleNodeProperties = SimpleNodeProperties()
    sub_resource_relationship: FakeEC2InstanceToAWSAccount = FakeEC2InstanceToAWSAccount()

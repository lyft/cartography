from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepSCALocationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('findingId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    path: PropertyRef = PropertyRef('path')
    start_line: PropertyRef = PropertyRef('startLine')
    start_col: PropertyRef = PropertyRef('startCol')
    end_line: PropertyRef = PropertyRef('endLine')
    end_col: PropertyRef = PropertyRef('endCol')
    url: PropertyRef = PropertyRef('url')


@dataclass(frozen=True)
class SemgrepSCALocToSemgrepSCAFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCALocation)<-[:LOCATED_AT]-(:SemgrepSCAFinding)
class SemgrepSCALocToSemgrepSCAFindingRelSchema(CartographyRelSchema):
    target_node_label: str = 'SemgrepSCAFinding'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('SCA_ID')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LOCATED_AT"
    properties: SemgrepSCALocToSemgrepSCAFindingRelProperties = SemgrepSCALocToSemgrepSCAFindingRelProperties()


@dataclass(frozen=True)
class SemgrepSCALocationSchema(CartographyNodeSchema):
    label: str = 'SemgrepSCALocation'
    properties: SemgrepSCALocationProperties = SemgrepSCALocationProperties()
    sub_resource_relationship: SemgrepSCALocToSemgrepSCAFindingRelSchema = SemgrepSCALocToSemgrepSCAFindingRelSchema()

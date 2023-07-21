from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepSCAFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef('ruleId', extra_index=True)
    repository: PropertyRef = PropertyRef('repositoryName', extra_index=True)
    summary: PropertyRef = PropertyRef('title')
    description: PropertyRef = PropertyRef('description')
    package_manager: PropertyRef = PropertyRef('ecosystem')
    severity: PropertyRef = PropertyRef('severity')
    cve_id: PropertyRef = PropertyRef('cveId', extra_index=True)
    reachability_check: PropertyRef = PropertyRef('reachability')
    reachability_condition: PropertyRef = PropertyRef('reachableIf')
    reachability: PropertyRef = PropertyRef('exposureType')
    dependency: PropertyRef = PropertyRef('matchedDependency')
    dependency_fix: PropertyRef = PropertyRef('closestSafeDependency')
    ref_urls: PropertyRef = PropertyRef('ref_urls')
    dependency_file: PropertyRef = PropertyRef('dependencyFileLocation_path')
    dependency_file_url: PropertyRef = PropertyRef('dependencyFileLocation_url')
    scan_time: PropertyRef = PropertyRef('openedAt')


@dataclass(frozen=True)
class SemgrepDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    slug: PropertyRef = PropertyRef('slug')


@dataclass(frozen=True)
class SemgrepSCAFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSCAFindingToSemgrepDeploymentSchema(CartographyRelSchema):
    target_node_label: str = 'SemgrepDeployment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DEPLOYMENT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSCAFindingToSemgrepDeploymentRelProperties = SemgrepSCAFindingToSemgrepDeploymentRelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSCAFindingToGithubRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'fullname': PropertyRef('repositoryName')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSCAFindingToGithubRepoRelProperties = SemgrepSCAFindingToGithubRepoRelProperties()


@dataclass(frozen=True)
class SemgrepDeploymentSchema(CartographyNodeSchema):
    label: str = 'SemgrepDeployment'
    properties: SemgrepDeploymentProperties = SemgrepDeploymentProperties()


@dataclass(frozen=True)
class SemgrepSCAFindingSchema(CartographyNodeSchema):
    label: str = 'SemgrepSCAFinding'
    properties: SemgrepSCAFindingNodeProperties = SemgrepSCAFindingNodeProperties()
    sub_resource_relationship: SemgrepSCAFindingToSemgrepDeploymentSchema = SemgrepSCAFindingToSemgrepDeploymentSchema()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSCAFindingToGithubRepoRel(),
        ],
    )


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
        {'id': PropertyRef('SCA_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LOCATED_AT"
    properties: SemgrepSCALocToSemgrepSCAFindingRelProperties = SemgrepSCALocToSemgrepSCAFindingRelProperties()


@dataclass(frozen=True)
class SemgrepSCALocationSchema(CartographyNodeSchema):
    label: str = 'SemgrepSCALocation'
    properties: SemgrepSCALocationProperties = SemgrepSCALocationProperties()
    sub_resource_relationship: SemgrepSCALocToSemgrepSCAFindingRelSchema = SemgrepSCALocToSemgrepSCAFindingRelSchema()

from dataclasses import dataclass

from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema

from cartography.models.core.common import PropertyRef

from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema, LinkDirection, TargetNodeMatcher, make_target_node_matcher

@dataclass(frozen=True)
class SCAFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    rule_id: PropertyRef = PropertyRef('ruleId', extra_index=True)
    repository: PropertyRef = PropertyRef('repositoryName', extra_index=True)
    deployment_id: PropertyRef = PropertyRef('deployment_id', set_in_kwargs=True)
    summary: PropertyRef = PropertyRef('title')
    description: PropertyRef = PropertyRef('description')
    package_manager: PropertyRef = PropertyRef('ecosystem')
    severity: PropertyRef = PropertyRef('severity')
    cve_id: PropertyRef = PropertyRef('cveId', extra_index=True)
    reachability_check: PropertyRef = PropertyRef('reachability')
    reachability: PropertyRef = PropertyRef('exposureType')
    dependency: PropertyRef = PropertyRef('matchedDependency')
    dependency_fix: PropertyRef = PropertyRef('closestSafeDependency')
    refUrls: PropertyRef = PropertyRef('ref_urls')
    dependency_file: PropertyRef = PropertyRef('dependencyFileLocation_path')
    dependency_file_url: PropertyRef = PropertyRef('dependencyFileLocation_url')
    scan_time: PropertyRef = PropertyRef('openedAt')

@dataclass(frozen=True)
class SemgrepDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    name: PropertyRef = PropertyRef('name')
    slug: PropertyRef = PropertyRef('slug')

@dataclass(frozen=True)
class SCAFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

@dataclass(frozen=True)
# (:SCAFinding)<-[:RETRIEVES]-(:SemgrepDeployment)
class SCAFindingToSemgrepDeploymentSchema(CartographyRelSchema):
    target_node_label: str = 'SemgrepDeployment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DEPLOYMENT_ID', set_in_kwargs=True),}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RETRIEVES"

@dataclass(frozen=True)
class SCAFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

@dataclass(frozen=True)
# (:SCAFinding)-[:FOUND_IN]->(:GitHubRepository)
class SCAFindingToGithubRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matchet: TargetNodeMatcher = make_target_node_matcher(
        {'fullname': PropertyRef('repository')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SCAFindingToGithubRepoRelProperties = SCAFindingToGithubRepoRelProperties()

@dataclass(frozen=True)
class SemgrepDeploymentSchema(CartographyNodeSchema):
    label: str = 'SemgrepDeployment'
    properties: SemgrepDeploymentProperties = SemgrepDeploymentProperties()

@dataclass(frozen=True)
class SCAFindingSchema(CartographyNodeSchema):
    label: str = 'SCAFinding'
    properties: SCAFindingNodeProperties = SCAFindingNodeProperties()
    sub_resource_relationships: SCAFindingToSemgrepDeploymentSchema = SCAFindingToSemgrepDeploymentSchema()
    relationships: list = [
        SCAFindingToGithubRepoRel(),
    ]

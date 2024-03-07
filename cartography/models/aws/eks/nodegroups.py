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
class EKSClusterNodeGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('nodegroupArn')
    consolelink: PropertyRef = PropertyRef('consolelink')
    arn: PropertyRef = PropertyRef('nodegroupArn', extra_index=True)
    name: PropertyRef = PropertyRef('nodegroupName', extra_index=True)
    region: PropertyRef = PropertyRef('region')
    created_at: PropertyRef = PropertyRef('createdAt')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    cluster_name: PropertyRef = PropertyRef('clusterName')
    capacity_type: PropertyRef = PropertyRef('capacityType')
    node_role: PropertyRef = PropertyRef('nodeRole')
    version: PropertyRef = PropertyRef('version')
    release_ersion: PropertyRef = PropertyRef('releaseVersion')
    status: PropertyRef = PropertyRef('status')
    ami_type: PropertyRef = PropertyRef('amiType')
    disk_tize: PropertyRef = PropertyRef('diskSize')


@dataclass(frozen=True)
class EKSClusterNodeGroupToEKSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EKSClusterNodeGroupToEKSCluster(CartographyRelSchema):
    target_node_label: str = 'EKSCluster'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('cluster_arn', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: EKSClusterNodeGroupToEKSClusterRelProperties = EKSClusterNodeGroupToEKSClusterRelProperties()


@dataclass(frozen=True)
class EKSClusterNodeGroupSchema(CartographyNodeSchema):
    label: str = 'EKSClusterNodeGroup'
    properties: EKSClusterNodeGroupNodeProperties = EKSClusterNodeGroupNodeProperties()
    sub_resource_relationship: EKSClusterNodeGroupToEKSCluster = EKSClusterNodeGroupToEKSCluster()

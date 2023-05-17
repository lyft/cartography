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
class EBSVolumeNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef('Arn', extra_index=True)
    id: PropertyRef = PropertyRef('Arn')
    volumeid: PropertyRef = PropertyRef('VolumeId', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    deleteontermination: PropertyRef = PropertyRef('DeleteOnTermination')
    availabilityzone: PropertyRef = PropertyRef('AvailabilityZone')
    createtime: PropertyRef = PropertyRef('CreateTime')
    encrypted: PropertyRef = PropertyRef('Encrypted')
    size: PropertyRef = PropertyRef('Size')
    state: PropertyRef = PropertyRef('State')
    outpostarn: PropertyRef = PropertyRef('OutpostArn')
    snapshotid: PropertyRef = PropertyRef('SnapshotId')
    iops: PropertyRef = PropertyRef('Iops')
    fastrestored: PropertyRef = PropertyRef('FastRestored')
    multiattachenabled: PropertyRef = PropertyRef('MultiAttachEnabled')
    type: PropertyRef = PropertyRef('VolumeType')
    kmskeyid: PropertyRef = PropertyRef('KmsKeyId')


@dataclass(frozen=True)
class EBSVolumeToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EBSVolumeToAwsAccountRelProperties = EBSVolumeToAwsAccountRelProperties()


@dataclass(frozen=True)
class EBSVolumeToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceArn')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: EBSVolumeToEC2InstanceRelProperties = EBSVolumeToEC2InstanceRelProperties()


@dataclass(frozen=True)
class EBSVolumeSchema(CartographyNodeSchema):
    label: str = 'EBSVolume'
    properties: EBSVolumeNodeProperties = EBSVolumeNodeProperties()
    sub_resource_relationship: EBSVolumeToAWSAccount = EBSVolumeToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EBSVolumeToEC2Instance(),
        ],
    )

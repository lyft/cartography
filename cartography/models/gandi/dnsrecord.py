from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GandiDNSRecordProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('rrset_name', extra_index=True)
    type: PropertyRef = PropertyRef('rrset_type')
    ttl: PropertyRef = PropertyRef('rrset_ttl')
    values: PropertyRef = PropertyRef('rrset_values')
    registered_domain: PropertyRef = PropertyRef('registered_domain')


@dataclass(frozen=True)
class ZoneToRecordRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:GandiDNSZone)-[:RESOURCE]->(:GandiDNSRecord)
class ZoneToRecordRel(CartographyRelSchema):
    target_node_label: str = 'GandiDNSZone'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'name': PropertyRef('registered_domain')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoneToRecordRelProperties = ZoneToRecordRelProperties()


@dataclass(frozen=True)
class RecordToIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:Ip)<-[:DNS_POINTS_TO]-(:GandiDNSRecord)
class RecordToIpRel(CartographyRelSchema):
    target_node_label: str = 'Ip'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('resolved_ip')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: RecordToIpRelProperties = RecordToIpRelProperties()


@dataclass(frozen=True)
class GandiDNSRecordSchema(CartographyNodeSchema):
    label: str = 'GandiDNSRecord'
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(['DNSRecord'])
    properties: GandiDNSRecordProperties = GandiDNSRecordProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ZoneToRecordRel(),
            RecordToIpRel(),
        ],
    )
    sub_resource_relationship: ZoneToRecordRel = ZoneToRecordRel()

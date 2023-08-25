import logging
from hashlib import md5
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from dateutil import parser as dt_parse

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gandi.utils import GandiAPI
from cartography.models.gandi.dnsrecord import GandiDNSRecordSchema
from cartography.models.gandi.dnszone import GandiDNSZoneSchema
from cartography.models.gandi.ip import IPSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    gandi_session: GandiAPI,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    domains = get(gandi_session)
    zones, records, ips = transform(domains)
    load_zones(neo4j_session, zones, records, ips, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(gandi_session: GandiAPI) -> List[Dict[str, Any]]:
    return gandi_session.get_domains()


@timeit
def transform(domains: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    zones: List[Dict[str, Any]] = []
    records: List[Dict[str, Any]] = []
    ips = set()

    for dom in domains:
        # Transform dates
        for k in list(dom['dates'].keys()):
            dom['dates'][k] = int(dt_parse.parse(dom['dates'][k]).timestamp() * 1000) if dom['dates'][k] else None
        # Create record from nameservers
        for ns in dom['nameservers']:
            records.append({
                "id": md5(f"{ns}+NS".encode()).hexdigest(),
                "rsset_name": "@",
                "rrset_type": "NS",
                "rsset_value": ns,
                "registered_domain": dom['fqdn'],
            })
        if "gandilivedns" in dom['services']:
            # Extract records
            for rec in dom.get('records', []):
                record_id = md5(f"{rec['rrset_name']}.{dom['fqdn']}+{rec['rrset_type']}".encode())
                # No value
                if len(rec['rrset_values']) == 0:
                    rec['id'] = record_id.hexdigest()
                    records.append(rec)
                    continue
                # 1 or more values
                for value in rec['rrset_values']:
                    record_id.update(value.encode())
                    rec_single = rec.copy()
                    rec_single['id'] = record_id.hexdigest()
                    rec_single['registered_domain'] = dom['fqdn']
                    # Split on IPs
                    if rec['rrset_type'] in ['A', 'AAAA']:
                        for ip in rec['rrset_values']:
                            splited_record = rec_single.copy()
                            splited_record['resolved_ip'] = ip
                            ips.add(ip)
                            records.append(splited_record)
                    else:
                        records.append(rec_single)
        zones.append(dom)
    # Format IPs
    formated_ips: List[Dict[str, Any]] = []
    for ip in ips:
        formated_ips.append({
            "id": ip,
            "ip": ip,
        })
    return zones, records, formated_ips


def load_zones(
    neo4j_session: neo4j.Session,
    zones: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    ips: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    # Save zones
    load(
        neo4j_session,
        GandiDNSZoneSchema(),
        zones,
        lastupdated=update_tag,
    )

    # Save Ips
    load(
        neo4j_session,
        IPSchema(),
        ips,
        lastupdated=update_tag,
    )

    # Save records
    load(
        neo4j_session,
        GandiDNSRecordSchema(),
        records,
        lastupdated=update_tag,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    #BUG: GraphJob.from_node_schema(GandiDNSZoneSchema(), common_job_parameters).run(neo4j_session)
    #BUG: GraphJob.from_node_schema(GandiDNSRecordSchema(), common_job_parameters).run(neo4j_session)
    pass

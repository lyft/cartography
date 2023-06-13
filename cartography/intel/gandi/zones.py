import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from dateutil import parser as dt_parse

from cartography.client.core.tx import load
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
    # TODO: Cleanup zones & domains (when linked to organization)


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
                "id": f"{ns}+NS",
                "rsset_name": "@",
                "rsset_type": "NS",
                "rsset_value": ns,
                "registered_domain": dom['fqdn'],
            })
        # Extract records
        for rec in dom['records']:
            rec['rrset_value'] = ','.join(rec['rrset_values'])
            if rec['rrset_name'] == '@':
                rec['id'] = rec['rrset_values'][0]
            else:
                rec['id'] = f"{rec['rrset_name']}.{dom['fqdn']}+{rec['rrset_type']}"
            rec['registered_domain'] = dom['fqdn']
            # Split on IPs
            if rec['rrset_type'] in ['A', 'AAAA']:
                if len(rec['rrset_values']) >= 1:
                    for ip in rec['rrset_values']:
                        splited_record = rec.copy()
                        splited_record['resolved_ip'] = ip
                        ips.add(ip)
                        records.append(splited_record)
                else:
                    records.append(rec)
            else:
                records.append(rec)
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

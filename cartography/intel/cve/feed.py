import gzip
import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cve_sync_metadata(neo4j_session: neo4j.Session) -> List[int]:
    get_cve_years_query = """
    MATCH (s:SyncMetadata)
    WHERE s.grouptype = "CVE" AND s.syncedtype = "year"
    RETURN s.groupid
    """
    results = neo4j_session.run(get_cve_years_query)
    years = []
    for r in results:
        years.append(int(r['s.groupid']))
    return years


@timeit
def get_cves(nist_cve_url: str, cve_type: str) -> Dict[Any, Any]:
    url = f"{nist_cve_url}/nvdcve-1.1-{cve_type}.json.gz"
    with requests.get(url, stream=True) as res:
        extracted = gzip.decompress(res.content)
    return json.loads(extracted)


def load_cves(neo4j_session: neo4j.Session, data: Dict[str, Any], update_tag: int) -> None:
    """
    Transform and load cve information
    """
    ingestion_cypher_query = """
    UNWIND $cves AS cve
        MERGE (c:CVE{id: cve.cve.CVE_data_meta.ID})
        ON CREATE SET c.id = cve.cve.CVE_data_meta.ID,
            c.firstseen = timestamp()
        SET c.assigner = cve.cve.CVE_data_meta.ASSIGNER,
            c.description_en = cve.cve.parsed_desc.en,
            c.references = cve.cve.parsed_reference_urls,
            c.problem_types = cve.cve.parsed_problem_types,
            c.vector_string = cve.impact.baseMetricV3.cvssV3.vectorString,
            c.attack_vector = cve.impact.baseMetricV3.cvssV3.attackVector,
            c.attack_complexity = cve.impact.baseMetricV3.cvssV3.attackComplexity,
            c.privileges_required = cve.impact.baseMetricV3.cvssV3.privilegesRequired,
            c.user_interaction = cve.impact.baseMetricV3.cvssV3.userInteraction,
            c.scope = cve.impact.baseMetricV3.cvssV3.scope,
            c.confidentiality_impact = cve.impact.baseMetricV3.cvssV3.confidentialityImpact,
            c.integrity_impact = cve.impact.baseMetricV3.cvssV3.integrityImpact,
            c.availability_impact = cve.impact.baseMetricV3.cvssV3.availabilityImpact,
            c.base_score = cve.impact.baseMetricV3.cvssV3.baseScore,
            c.base_severity = cve.impact.baseMetricV3.cvssV3.baseSeverity,
            c.exploitability_score = cve.impact.baseMetricV3.exploitabilityScore,
            c.impact_score = cve.impact.baseMetricV3.impactScore,
            c.published_date = cve.publishedDate,
            c.last_modified_date = cve.lastModifiedDate,
            c.lastupdated = $update_tag
        WITH c, cve
        MATCH (v:SpotlightVulnerability{id: cve.vuln_id})
        MERGE (v)-[hc:HAS_CVE]->(c)
        ON CREATE SET hc.firstseen = timestamp()
        SET hc.lastupdated = $update_tag
    """
    for cve in data["CVE_Items"]:
        parsed_desc = {}
        for desc in cve['cve']['description'].get('description_data', []):
            parsed_desc[desc["lang"]] = (desc['value'])
        cve["cve"]["parsed_desc"] = parsed_desc

        parsed_reference_urls = []
        for reference in cve['cve']['references'].get('reference_data', []):
            parsed_reference_urls.append(reference['url'])
        cve["cve"]["parsed_reference_urls"] = parsed_reference_urls

        parsed_problem_types = []
        for problemtype_data in cve['cve']['problemtype']['problemtype_data']:
            for problemtype in problemtype_data["description"]:
                parsed_problem_types.append(problemtype['value'])
        cve["cve"]["parsed_problem_types"] = parsed_problem_types

    neo4j_session.run(
        ingestion_cypher_query,
        cves=data["CVE_Items"],
        update_tag=update_tag,
    )

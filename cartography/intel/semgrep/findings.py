
import logging
from typing import Any, Dict, List
import neo4j
import requests

from cartography.util import timeit

from cartography.models.semgrep.findings import SCAFindingSchema, SemgrepDeploymentSchema

from cartography.client.core.tx import load

from cartography.graph.job import GraphJob

logger = logging.getLogger(__name__)
@timeit
def get_deployment(semgrep_app_token: str) -> Dict[str, Any]:
    """
    Gets the deployment associated with the passed Semgrep App token.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    """
    deployment = {}
    deployment_url = 'https://semgrep.dev/api/v1/deployments'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}"
    }
    response = requests.get(deployment_url, headers=headers)
    response.raise_for_status()
    try:
        if response.status_code == 200:
            data = response.json()
            deployment['id'] = data["deployments"][0]['id']
            deployment['name'] = data["deployments"][0]['name']
            deployment['slug'] = data["deployments"][0]['slug']
    except requests.RequestException as e:
        logger.error("Could not complete request to the deployments Semgrep API: %s", e, exc_info=e)
        raise e
    except Exception as e:
        logger.error("Erorr retrieving Semgrep deployment info: %s", e, exc_info=e)
        raise e
    return deployment


@timeit
def get_sca_vulns(semgrep_app_token: str, deployment_id: str) -> List[Dict[str, Any]]:
    """
    Gets the SCA vulns associated with the passed Semgrep App token and deployment id.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment id to use for retrieving SCA vulns.
    """
    all_vulns = []
    sca_url = f"https://semgrep.dev/api/sca/deployments/{deployment_id}/vulns"
    has_more = True
    cursor = ""
    prev_request = None
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}"
    }

    while has_more:
        params = {}
        if cursor:
            params = {"cursor": cursor}
        try:
            response = requests.get(sca_url, params=params, headers=headers)
            response.raise_for_status()
            if prev_request == response.request.url:
                logger.warning("Duplicate request detected. Breaking the loop to avoid infinite requests.")
                break
            prev_request = response.request.url
            if response.status_code == 200:
                data = response.json()
                vulns = data["vulns"]
                cursor = data.get("cursor")
                has_more = data.get("hasMore", False)
                all_vulns.extend(vulns)
        except requests.RequestException as e:
            logger.error("Could not complete request to the SCA Semgrep API: %s", e, exc_info=e)
            raise e
        except Exception as e:
            logger.error("Erorr retrieving Semgrep SCA vulns info: %s", e, exc_info=e)
            raise e
    return all_vulns

def transform_sca_vulns(raw_vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the raw SCA vulns response from Semgrep API into a list of dicts that can be used to create the SCAFinding nodes.
    """
    vulns_set = set()
    for vuln in raw_vulns:
        sca_vuln = {}
        # Mandatory fields
        unique_id = f"{vuln['repositoryName']}|{vuln['advisory']['ruleId']}"
        sca_vuln['id'] = unique_id
        sca_vuln['repositoryName'] = vuln['repositoryName']
        sca_vuln['ruleId'] = vuln['advisory']['ruleId']
        sca_vuln['title'] = vuln['advisory']['title']
        sca_vuln['description'] = vuln['advisory']['description']
        sca_vuln['ecosystem'] = vuln['advisory']['ecosystem']
        sca_vuln['severity'] = vuln['advisory']['severity']
        sca_vuln['cveId'] = vuln['advisory']['references']['cveIds'][0]
        sca_vuln['reachability'] = vuln['reachability']
        sca_vuln['exposureType'] = vuln['exposureType']
        dependency = f"{vuln['matchedDependency']['name']}|{vuln['matchedDependency']['versionSpecifier']}"
        sca_vuln['matchedDependency'] = dependency
        dependency_fix = f"{vuln['closestSafeDependency']['name']}|{vuln['closestSafeDependency']['versionSpecifier']}"
        sca_vuln['closestSafeDependency'] = dependency_fix
        sca_vuln['dependencyFileLocation_path'] = vuln['dependencyFileLocation']['path']
        sca_vuln['dependencyFileLocation_url'] = vuln['dependencyFileLocation']['url']
        # Optional fields
        if not vuln['advisory'].get('references', {}).get('urls'):
            sca_vuln['ref_urls'] = None
        sca_vuln['ref_urls'] = ','.join(vuln['advisory']['references']['urls'])
        sca_vuln['openedAt'] = vuln.get('openedAt')
        vulns_set.add(sca_vuln)
    return list(vulns_set)

def load_semgrep_deployment(neo4j_session: neo4j.Session,
                            deployment: Dict[str, Any],
                            update_tag: int) -> None:
    logger.info(f"Loading Semgrep deployment info {deployment} into the graph...")
    load(
        neo4j_session,
        SemgrepDeploymentSchema(),
        deployment,
        update_tag,
    )

@timeit
def load_semgrep_sca_vulns(neo4j_session: neo4j.Session,
                           vulns: List[Dict[str, Any]],
                           deployment_id: str,
                           update_tag: int) -> None:
    logger.info(f"Loading Semgrep SCA vulns info into the graph.")
    load(
        neo4j_session,
        SCAFindingSchema(),
        vulns,
        update_tag,
        DEPLOYMENT_ID=deployment_id,
    )

@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.info("Running Semgrep SCA findings cleanup job.")
    cleanup_job = GraphJob.from_node_schema(SCAFindingSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

@timeit
def sync(neo4j_sesion: neo4j.Session, semgrep_app_token: str, update_tag:str, common_job_parameters: Dict[str, Any]) -> None:
    logger.info("Running Semgrep SCA findings sync job.")
    semgrep_deployment = get_deployment(semgrep_app_token)
    load_semgrep_deployment(neo4j_sesion, semgrep_deployment, update_tag)
    raw_vulns = get_sca_vulns(semgrep_app_token, semgrep_deployment["id"])
    vulns = transform_sca_vulns(raw_vulns)
    load_semgrep_sca_vulns(neo4j_sesion, vulns, semgrep_deployment["id"], update_tag)
    cleanup(neo4j_sesion, common_job_parameters)

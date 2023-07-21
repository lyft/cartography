import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.semgrep.findings import SemgrepDeploymentSchema
from cartography.models.semgrep.findings import SemgrepSCAFindingSchema
from cartography.models.semgrep.findings import SemgrepSCALocationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_deployment(semgrep_app_token: str) -> List[Dict[str, Any]]:
    """
    Gets the deployment associated with the passed Semgrep App token.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    """
    deployment = {}
    deployment_url = "https://semgrep.dev/api/v1/deployments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }
    response = requests.get(deployment_url, headers=headers)
    response.raise_for_status()
    try:
        if response.status_code == 200:
            data = response.json()
            deployment["id"] = data["deployments"][0]["id"]
            deployment["name"] = data["deployments"][0]["name"]
            deployment["slug"] = data["deployments"][0]["slug"]
    except requests.RequestException as e:
        logger.error(
            "Could not complete request to the deployments Semgrep API: %s",
            e,
            exc_info=e,
        )
        raise e
    except Exception as e:
        logger.error("Erorr retrieving Semgrep deployment info: %s", e, exc_info=e)
        raise e
    return [deployment]


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
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    while has_more:
        params = {}
        if cursor:
            params = {"cursor": cursor}
        try:
            response = requests.get(sca_url, params=params, headers=headers)
            response.raise_for_status()
            if prev_request == response.request.url:
                logger.warning(
                    "Duplicate request detected. Breaking the loop to avoid infinite requests.",
                )
                break
            prev_request = response.request.url
            if response.status_code == 200:
                data = response.json()
                vulns = data["vulns"]
                cursor = data.get("cursor")
                has_more = data.get("hasMore", False)
                all_vulns.extend(vulns)
        except requests.RequestException as e:
            logger.error(
                "Could not complete request to the SCA Semgrep API: %s", e, exc_info=e,
            )
            raise e
        except Exception as e:
            logger.error("Erorr retrieving Semgrep SCA vulns info: %s", e, exc_info=e)
            raise e
    return all_vulns


def transform_sca_vulns(raw_vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the raw SCA vulns response from Semgrep API into a list of dicts
    that can be used to create the SemgrepSCAFinding nodes.
    """
    vulns = []
    for vuln in raw_vulns:
        sca_vuln: Dict[str, Any] = {}
        # Mandatory fields
        unique_id = f"{vuln['repositoryName']}|{vuln['advisory']['ruleId']}"
        sca_vuln["id"] = unique_id
        sca_vuln["repositoryName"] = vuln["repositoryName"]
        sca_vuln["ruleId"] = vuln["advisory"]["ruleId"]
        sca_vuln["title"] = vuln["advisory"]["title"]
        sca_vuln["description"] = vuln["advisory"]["description"]
        sca_vuln["ecosystem"] = vuln["advisory"]["ecosystem"]
        sca_vuln["severity"] = vuln["advisory"]["severity"]
        sca_vuln["cveId"] = vuln["advisory"]["references"]["cveIds"][0]
        sca_vuln["reachability"] = vuln["advisory"]["reachability"]
        sca_vuln["reachableIf"] = vuln["advisory"]["reachableIf"]
        sca_vuln["exposureType"] = vuln["exposureType"]
        dependency = f"{vuln['matchedDependency']['name']}|{vuln['matchedDependency']['versionSpecifier']}"
        sca_vuln["matchedDependency"] = dependency
        dependency_fix = f"{vuln['closestSafeDependency']['name']}|{vuln['closestSafeDependency']['versionSpecifier']}"
        sca_vuln["closestSafeDependency"] = dependency_fix
        sca_vuln["dependencyFileLocation_path"] = vuln["dependencyFileLocation"]["path"]
        sca_vuln["dependencyFileLocation_url"] = vuln["dependencyFileLocation"]["url"]
        # Optional fields
        ref_urls = vuln["advisory"].get("references", {}).get("urls", [])
        if ref_urls:
            sca_vuln["ref_urls"] = ",".join(ref_urls)
        sca_vuln["openedAt"] = vuln.get("openedAt", None)
        usages_list = []
        for usage in vuln.get("usages", []):
            usage_dict = {}
            usage_dict["findingId"] = usage["findingId"]
            usage_dict["path"] = usage["location"]["path"]
            usage_dict["startLine"] = usage["location"]["startLine"]
            usage_dict["startCol"] = usage["location"]["startCol"]
            usage_dict["endLine"] = usage["location"]["endLine"]
            usage_dict["endCol"] = usage["location"]["endCol"]
            usage_dict["url"] = usage["location"]["url"]
            usages_list.append(usage_dict)
        sca_vuln["usages"] = usages_list
        vulns.append(sca_vuln)
    return vulns


@timeit
def load_semgrep_deployment(
    neo4j_session: neo4j.Session, deployment: List[Dict[str, Any]], update_tag: int,
) -> None:
    logger.info(f"Loading Semgrep deployment info {deployment} into the graph...")
    load(
        neo4j_session,
        SemgrepDeploymentSchema(),
        deployment,
        lastupdated=update_tag,
    )


@timeit
def load_semgrep_sca_vulns(
    neo4j_session: neo4j.Session,
    vulns: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(vulns)} Semgrep SCA vulns info into the graph.")
    load(
        neo4j_session,
        SemgrepSCAFindingSchema(),
        vulns,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )
    for vuln in vulns:
        if vuln.get("usages"):
            load(
                neo4j_session,
                SemgrepSCALocationSchema(),
                vuln["usages"],
                lastupdated=update_tag,
                SCA_ID=vuln["id"],
            )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep SCA findings cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        SemgrepSCAFindingSchema(), common_job_parameters,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_sesion: neo4j.Session,
    semgrep_app_token: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep SCA findings sync job.")
    semgrep_deployment = get_deployment(semgrep_app_token)
    load_semgrep_deployment(neo4j_sesion, semgrep_deployment, update_tag)
    common_job_parameters["DEPLOYMENT_ID"] = semgrep_deployment[0]["id"]
    raw_vulns = get_sca_vulns(semgrep_app_token, semgrep_deployment[0]["id"])
    vulns = transform_sca_vulns(raw_vulns)
    load_semgrep_sca_vulns(neo4j_sesion, vulns, semgrep_deployment[0]["id"], update_tag)
    cleanup(neo4j_sesion, common_job_parameters)

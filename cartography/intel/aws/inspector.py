import logging
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import batch
from cartography.util import run_cleanup_job
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_inspector_findings(
    session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
) -> List[Dict]:
    """
    We must list_findings by filtering the request, otherwise the request could tiemout.
    First, we filter by account_id. And since there may be millions of CLOSED findings that may never go away,
    we will only fetch those in ACTIVE or SUPPRESSED statuses.
    list_members will get us all the accounts that
    have delegated access to the account specified by current_aws_account_id.
    """
    client = session.client("inspector2", region_name=region)

    members = aws_paginate(client, "list_members", "members")
    # the current host account may not be considered a "member", but we still fetch its findings
    accounts = [current_aws_account_id] + [m["accountId"] for m in members]

    findings = []
    for account in accounts:
        logger.info(f"Getting findings for member account {account} in region {region}")
        findings.extend(
            aws_paginate(
                client,
                "list_findings",
                "findings",
                filterCriteria={
                    "awsAccountId": [
                        {
                            "comparison": "EQUALS",
                            "value": account,
                        },
                    ],
                    "findingStatus": [
                        {
                            "comparison": "NOT_EQUALS",
                            "value": "CLOSED",
                        },
                    ],
                },
            ),
        )
    return findings


def transform_inspector_findings(results: List[Dict]) -> Tuple[List, List]:
    findings_list: List[Dict] = []
    packages: Dict[str, Any] = {}

    for f in results:
        finding: Dict = {}
        # Finding Meta Information
        finding["id"] = f["findingArn"]
        finding["arn"] = f["findingArn"]
        finding["name"] = f["title"]
        finding["firstobservedat"] = f["firstObservedAt"]
        finding["lastobservedat"] = f["lastObservedAt"]
        finding["status"] = f["status"]
        finding["updatedat"] = f["updatedAt"]
        finding["awsaccount"] = f["awsAccountId"]
        finding["description"] = f["description"]
        finding["type"] = f["type"]

        # Resource information of finding
        # AWS_EC2_INSTANCE will include NETWORK_REACHABILITY
        if f["resources"][0]["type"] == "AWS_EC2_INSTANCE":
            finding["instanceid"] = f["resources"][0]["id"]
        if f["resources"][0]["type"] == "AWS_LAMBDA_FUNCTION":
            lambdaarn = f["resources"][0]["id"]
            version = f["resources"][0]["details"]["awsLambdaFunction"]["version"]
            # The value here may be similar to arn:aws:lambda:{region}}:{acc_id}:function:{func_name}:{version}
            id_version_split = lambdaarn.rsplit(":", 1)
            if len(id_version_split) == 2 and version == id_version_split[1]:
                lambdaarn = id_version_split[0]
            finding["lambdaid"] = lambdaarn
        if f["resources"][0]["type"] == "AWS_ECR_CONTAINER_IMAGE":
            finding["ecrimageid"] = f["resources"][0]["id"]
        if f["resources"][0]["type"] == "AWS_ECR_REPOSITORY":
            finding["ecrrepositoryid"] = f["resources"][0]["id"]

        # Finding Vuln Data
        finding["severity"] = f["severity"]
        finding["remediation"] = f["remediation"].get("recommendation", {}).get("text")
        if f.get("inspectorScoreDetails"):
            finding["cvssscore"] = f["inspectorScoreDetails"]["adjustedCvss"]["score"]
        if finding["type"] == "NETWORK_REACHABILITY":
            if f.get("networkReachabilityDetails"):
                finding["protocol"] = f["networkReachabilityDetails"]["protocol"]
                finding["portrangebegin"] = f["networkReachabilityDetails"][
                    "openPortRange"
                ]["begin"]
                finding["portrangeend"] = f["networkReachabilityDetails"][
                    "openPortRange"
                ]["end"]
                finding["portrange"] = _port_range_string(
                    f["networkReachabilityDetails"],
                )
        # Get information about impacted package, and package vuln details
        else:
            vuln_data, new_packages = _process_packages(
                f["packageVulnerabilityDetails"],
                f["awsAccountId"],
                f["findingArn"],
            )
            if vuln_data.get("impactedfilepaths"):
                finding["impactedfilepaths"] = "|| ".join(
                    vuln_data["impactedfilepaths"],
                )
            if vuln_data.get("fixedinversions"):
                finding["fixedinversions"] = "|| ".join(vuln_data["fixedinversions"])
            if vuln_data.get("impactedpackagemanagers"):
                finding["impactedpackagemanagers"] = "|| ".join(
                    vuln_data["impactedpackagemanagers"],
                )
            if vuln_data.get("packageremediations"):
                finding["packageremediations"] = "|| ".join(
                    vuln_data["packageremediations"],
                )
            if vuln_data.get("sourceLayerHash"):
                finding["sourceLayerHash"] = "|| ".join(
                    vuln_data["sourceLayerHash"],
                )

            finding["vulnerablepackageids"] = ", ".join(new_packages.keys())
            packages = {**packages, **new_packages}

        if f.get("packageVulnerabilityDetails"):
            finding["vulnerabilityid"] = f["packageVulnerabilityDetails"][
                "vulnerabilityId"
            ]
            finding["referenceurls"] = f["packageVulnerabilityDetails"].get(
                "referenceUrls",
            )
            finding["relatedvulnerabilities"] = f["packageVulnerabilityDetails"].get(
                "relatedVulnerabilities",
            )
            finding["source"] = f["packageVulnerabilityDetails"].get("source")
            finding["sourceurl"] = f["packageVulnerabilityDetails"].get("sourceUrl")
            finding["vendorcreatedat"] = f["packageVulnerabilityDetails"].get(
                "vendorCreatedAt",
            )
            finding["vendorseverity"] = f["packageVulnerabilityDetails"].get(
                "vendorSeverity",
            )
            finding["vendorupdatedat"] = f["packageVulnerabilityDetails"].get(
                "vendorUpdatedAt",
            )
        findings_list.append(finding)
    packages_list = transform_inspector_packages(packages)
    return findings_list, packages_list


def transform_inspector_packages(packages: Dict[str, Any]) -> List[Dict]:
    packages_list: List[Dict] = []
    for package_id in packages.keys():
        packages_list.append(packages[package_id])

    return packages_list


def _process_packages(
    package_details: Dict[str, Any],
    aws_account_id: str,
    finding_arn: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    vuln_details: Dict[str, Any] = defaultdict(lambda: [])
    packages: Dict[str, Any] = {}
    package_vuln_data = package_details.get("packageVulnerabilityDetails")
    # Traverse the package vuln data
    if package_vuln_data:
        vuln_details["referenceurls"] = package_vuln_data.get("referenceUrls")

        vuln_details["relatedvulnerabilities"] = package_vuln_data.get(
            "relatedVulnerabilities",
        )
        vuln_details["source"] = package_vuln_data.get("source")
        vuln_details["sourceurl"] = package_vuln_data.get("sourceUrl")
        vuln_details["vendorcreatedat"] = package_vuln_data.get("vendorCreatedAt")
        vuln_details["vendorseverity"] = package_vuln_data.get("vendorSeverity")
        vuln_details["vendorupdatedat"] = package_vuln_data.get("vendorUpdatedAt")
        vuln_details["vulnerabilityid"] = package_vuln_data.get("vulnerabilityId")
    # Some vuln data is in the package as well
    # we're gonna make one package per uniqueID
    for package in package_details["vulnerablePackages"]:
        new_package = {}
        new_package["id"] = (
            f"{package.get('name', '')}|"
            f"{package.get('arch', '')}|"
            f"{package.get('version', '')}|"
            f"{package.get('release', '')}|"
            f"{package.get('epoch', '')}"
        )
        new_package["name"] = package.get("name")
        new_package["arch"] = package.get("arch")
        new_package["version"] = package.get("version")
        new_package["release"] = package.get("release")
        new_package["epoch"] = package.get("epoch")

        if package.get("filePath"):
            vuln_details["impactedfilepaths"].append(package.get("filePath"))
        if package.get("fixedinversions"):
            vuln_details["fixedinversions"].append(package.get("fixedInVersion"))
        if package.get("packageManager"):
            vuln_details["impactedpackagemanagers"].append(
                package.get("packageManager"),
            )
        if package.get("packageremediations"):
            vuln_details["packageremediations"].append(package.get("remediation"))
        if package.get("sourceLayerHash"):
            vuln_details["sourcelayerhash"].append(package.get("sourceLayerHash"))

        packages[new_package["id"]] = new_package
    return dict(vuln_details), packages


def _port_range_string(details: Dict) -> str:
    begin = details["openPortRange"]["begin"]
    end = details["openPortRange"]["end"]
    return f"{begin}-{end}"


def _load_findings_tx(
    tx: neo4j.Transaction,
    findings: List[Dict],
    region: str,
    aws_update_tag: int,
) -> None:
    query = """
    UNWIND $Findings as new_finding
        MERGE (finding:AWSInspectorFinding{id: new_finding.id})
        ON CREATE SET finding.firstseen = timestamp(),
            finding.arn = new_finding.arn,
            finding.region = $Region,
            finding.awsaccount = new_finding.awsaccount
        SET finding.lastupdated = $UpdateTag,
            finding.name = new_finding.name,
            finding.instanceid = new_finding.instanceid,
            finding.lambdaid = new_finding.lambdaid,
            finding.ecrimageid = new_finding.ecrimageid,
            finding.ecrrepositoryid = new_finding.ecrrepositoryid,
            finding.severity = new_finding.severity,
            finding.firstobservedat = new_finding.firstobservedat,
            finding.lastobservedat = new_finding.lastobservedat,
            finding.updatedat = new_finding.updatedat,
            finding.description = new_finding.description,
            finding.type = new_finding.type,
            finding.cvssscore = new_finding.cvssscore,
            finding.protocol = new_finding.protocol,
            finding.portrange = new_finding.portrange,
            finding.portrangebegin = new_finding.portrangebegin,
            finding.portrangeend = new_finding.portrangeend,
            finding.impactedfilepaths = new_finding.impactedfilepaths,
            finding.fixedinversions = new_finding.fixedinversions,
            finding.impactedpackagemanagers = new_finding.impactedpackagemanagers,
            finding.packageremediations = new_finding.packageremediations,
            finding.sourcelayerhash = new_finding.sourceLayerHash,
            finding.vulnerabilityid = new_finding.vulnerabilityid,
            finding.referenceurls = new_finding.referenceurls,
            finding.relatedvulnerabilities = new_finding.relatedvulnerabilities,
            finding.remediation = new_finding.remediation,
            finding.source = new_finding.source,
            finding.sourceurl = new_finding.sourceurl,
            finding.status = new_finding.status,
            finding.vendorcreatedat = new_finding.vendorcreatedat,
            finding.vendorseverity = new_finding.vendorseverity,
            finding.vendorupdatedat = new_finding.vendorupdatedat,
            finding.vulnerablepackageids = new_finding.vulnerablepackageids,
            finding:Risk
        WITH finding
        MATCH (account:AWSAccount{id: finding.awsaccount})
        MERGE (account)-[r0:RESOURCE]->(finding)
        ON CREATE SET r0.firstseen = timestamp()
        SET r0.lastupdated = $UpdateTag
        WITH finding
        MATCH (package:AWSInspectorPackage) where finding.vulnerablepackageids CONTAINS package.id
        MERGE (finding)-[r1:AFFECTS]->(package)
        SET r1.lastupdated = $UpdateTag
    """

    query2 = """
    UNWIND $Findings as new_finding
        MATCH (finding:AWSInspectorFinding{id: new_finding.id})
        WITH finding
        MATCH (lambda:AWSLambda) where finding.lambdaid = lambda.id
        MERGE (lambda)<-[r2:PRESENT_ON]-(finding)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $UpdateTag
    """

    query3 = """
    UNWIND $Findings as new_finding
        MATCH (finding:AWSInspectorFinding{id: new_finding.id})
        WITH finding
        MATCH (instance:EC2Instance) where finding.instanceid = instance.id
        MERGE (instance)<-[r3:PRESENT_ON]-(finding)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = $UpdateTag
    """

    query4 = """
    UNWIND $Findings as new_finding
        MATCH (finding:AWSInspectorFinding{id: new_finding.id})
        WITH finding
        MATCH (repo:ECRRepository{id: finding.ecrrepositoryid})
        MERGE (repo)<-[r4:PRESENT_ON]-(finding)
        ON CREATE SET r4.firstseen = timestamp()
        SET r4.lastupdated = $UpdateTag
    """

    query5 = """
    UNWIND $Findings as new_finding
        MATCH (finding:AWSInspectorFinding{id: new_finding.id})
        WITH finding
        MATCH (image:ECRImage{id: finding.ecrimageid})
        MERGE (image)<-[r5:PRESENT_ON]-(finding)
        ON CREATE SET r5.firstseen = timestamp()
        SET r5.lastupdated = $UpdateTag
    """
    queries = [query, query2, query3, query4, query5]
    for query in queries:
        tx.run(
            query,
            Findings=findings,
            UpdateTag=aws_update_tag,
            Region=region,
        )


@timeit
def load_inspector_findings(
    neo4j_session: neo4j.Session,
    findings: List[Dict],
    region: str,
    aws_update_tag: int,
) -> None:
    for i, findings_batch in enumerate(batch(findings), start=1):
        logger.info(f"Loading batch number {i}")
        neo4j_session.write_transaction(
            _load_findings_tx,
            findings=findings_batch,
            region=region,
            aws_update_tag=aws_update_tag,
        )


def _load_packages_tx(
    tx: neo4j.Transaction,
    packages: List[Dict],
    region: str,
    aws_update_tag: int,
) -> None:
    query = """
    UNWIND $Packages as new_package
        MERGE (package:AWSInspectorPackage{id: new_package.id})
        ON CREATE SET package.firstseen = timestamp(),
            package.region = $Region,
            package.awsaccount = new_package.awsaccount,
            package.findingarn = new_package.findingarn
        SET package.lastupdated = $UpdateTag,
            package.name = new_package.name,
            package.arch = new_package.arch,
            package.version = new_package.version,
            package.release = new_package.release,
            package.epoch = new_package.epoch,
            package.manager = new_package.packageManager
        WITH package
        MATCH (account:AWSAccount{id: package.awsaccount})
        MERGE (account)-[r:RESOURCE]->(package)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
    """

    tx.run(
        query,
        Packages=packages,
        UpdateTag=aws_update_tag,
        Region=region,
    )


@timeit
def load_inspector_packages(
    neo4j_session: neo4j.Session,
    packages: List[Dict],
    region: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_packages_tx,
        packages=packages,
        region=region,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_inspector_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS Inspector findings for account {current_aws_account_id} and region {region}",
        )
        findings = get_inspector_findings(boto3_session, region, current_aws_account_id)
        finding_data, package_data = transform_inspector_findings(findings)
        logger.info(f"Loading {len(package_data)} packages")
        load_inspector_packages(neo4j_session, package_data, region, update_tag)
        logger.info(f"Loading {len(finding_data)} findings")
        load_inspector_findings(neo4j_session, finding_data, region, update_tag)
        cleanup(neo4j_session, common_job_parameters)

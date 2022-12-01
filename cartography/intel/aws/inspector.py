import logging
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
    '''
    We must list_findings by filtering the request, otherwise the request could tiemout.
    First, we filter by account_id. And since there may be millions of CLOSED findings that may never go away,
    we will only fetch those in ACTIVE or SUPPRESSED statuses.
    list_members will get us all the accounts that
    have delegated access to the account specified by current_aws_account_id.
    '''
    client = session.client('inspector2', region_name=region)

    members = aws_paginate(client, 'list_members', 'members')
    # the current host account may not be considered a "member", but we still fetch its findings
    accounts = [current_aws_account_id] + [m['accountId'] for m in members]

    findings = []
    for account in accounts:
        logger.info(f'Getting findings for member account {account} in region {region}')
        findings.extend(
            aws_paginate(
                client, 'list_findings', 'findings', filterCriteria={
                    'awsAccountId': [
                        {
                            'comparison': 'EQUALS',
                            'value': account,
                        },
                    ],
                    'findingStatus': [
                        {
                            'comparison': 'NOT_EQUALS',
                            'value': 'CLOSED',
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

        finding['id'] = f['findingArn']
        finding['arn'] = f['findingArn']
        finding['severity'] = f['severity']
        finding['name'] = f['title']
        finding['firstobservedat'] = f['firstObservedAt']
        finding['updatedat'] = f['updatedAt']
        finding['awsaccount'] = f['awsAccountId']
        finding['description'] = f['description']
        finding['type'] = f['type']
        finding['status'] = f['status']
        if f.get('inspectorScoreDetails'):
            finding['cvssscore'] = f['inspectorScoreDetails']['adjustedCvss']['score']
        if f['resources'][0]['type'] == "AWS_EC2_INSTANCE":
            finding['instanceid'] = f['resources'][0]['id']
        if f['resources'][0]['type'] == "AWS_ECR_CONTAINER_IMAGE":
            finding['ecrimageid'] = f['resources'][0]['id']
        if f['resources'][0]['type'] == "AWS_ECR_REPOSITORY":
            finding['ecrrepositoryid'] = f['resources'][0]['id']
        if f.get('networkReachabilityDetails'):
            finding['protocol'] = f['networkReachabilityDetails']['protocol']
            finding['portrangebegin'] = f['networkReachabilityDetails']['openPortRange']['begin']
            finding['portrangeend'] = f['networkReachabilityDetails']['openPortRange']['end']
            finding['portrange'] = _port_range_string(f['networkReachabilityDetails'])
        if f.get('packageVulnerabilityDetails'):
            finding['vulnerabilityid'] = f['packageVulnerabilityDetails']['vulnerabilityId']
            finding['referenceurls'] = f['packageVulnerabilityDetails'].get('referenceUrls')
            finding['relatedvulnerabilities'] = f['packageVulnerabilityDetails'].get('relatedVulnerabilities')
            finding['source'] = f['packageVulnerabilityDetails'].get('source')
            finding['sourceurl'] = f['packageVulnerabilityDetails'].get('sourceUrl')
            finding['vendorcreatedat'] = f['packageVulnerabilityDetails'].get('vendorCreatedAt')
            finding['vendorseverity'] = f['packageVulnerabilityDetails'].get('vendorSeverity')
            finding['vendorupdatedat'] = f['packageVulnerabilityDetails'].get('vendorUpdatedAt')

            new_packages = _process_packages(f['packageVulnerabilityDetails'], f['awsAccountId'], f['findingArn'])
            finding['vulnerablepackageids'] = list(new_packages.keys())
            packages = {**packages, **new_packages}

        findings_list.append(finding)
    packages_list = transform_inspector_packages(packages)
    return findings_list, packages_list


def transform_inspector_packages(packages: Dict[str, Any]) -> List[Dict]:
    packages_list: List[Dict] = []
    for package_id in packages.keys():
        packages_list.append(packages[package_id])

    return packages_list


def _process_packages(package_details: Dict[str, Any], aws_account_id: str, finding_arn: str) -> Dict[str, Any]:
    packages: Dict[str, Any] = {}
    for package in package_details['vulnerablePackages']:
        new_package = {}
        new_package['id'] = (
            f"{package.get('name', '')}|"
            f"{package.get('arch', '')}|"
            f"{package.get('version', '')}|"
            f"{package.get('release', '')}|"
            f"{package.get('epoch', '')}"
        )
        new_package['name'] = package.get('name')
        new_package['arch'] = package.get('arch')
        new_package['version'] = package.get('version')
        new_package['release'] = package.get('release')
        new_package['epoch'] = package.get('epoch')
        new_package['manager'] = package.get("packageManager")
        new_package['filepath'] = package.get('filePath')
        new_package['fixedinversion'] = package.get('fixedInVersion')
        new_package['sourcelayerhash'] = package.get('sourceLayerHash')
        new_package['awsaccount'] = aws_account_id
        new_package['findingarn'] = finding_arn

        packages[new_package['id']] = new_package

    return packages


def _port_range_string(details: Dict) -> str:
    begin = details['openPortRange']['begin']
    end = details['openPortRange']['end']
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
            finding.name = new_finding.title,
            finding.instanceid = new_finding.instanceid,
            finding.ecrimageid = new_finding.ecrimageid,
            finding.ecrrepositoryid = new_finding.ecrrepositoryid,
            finding.severity = new_finding.severity,
            finding.firstobservedat = new_finding.firstobservedat,
            finding.updatedat = new_finding.updatedat,
            finding.description = new_finding.description,
            finding.type = new_finding.type,
            finding.cvssscore = new_finding.cvssscore,
            finding.protocol = new_finding.protocol,
            finding.portrange = new_finding.portrange,
            finding.portrangebegin = new_finding.portrangebegin,
            finding.portrangeend = new_finding.portrangeend,
            finding.vulnerabilityid = new_finding.vulnerabilityid,
            finding.referenceurls = new_finding.referenceurls,
            finding.relatedvulnerabilities = new_finding.relatedvulnerabilities,
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
        MERGE (account)-[r:RESOURCE]->(finding)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
        WITH finding
        MATCH (instance:EC2Instance{id: finding.instanceid})
        MERGE (instance)<-[r2:AFFECTS]-(finding)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $UpdateTag
        WITH finding
        MATCH (repo:ECRRepository{id: finding.ecrrepositoryid})
        MERGE (repo)<-[r3:AFFECTS]-(finding)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = $UpdateTag
        WITH finding
        MATCH (image:ECRImage{id: finding.ecrimageid})
        MERGE (image)<-[r4:AFFECTS]-(finding)
        ON CREATE SET r4.firstseen = timestamp()
        SET r4.lastupdated = $UpdateTag
    """

    tx.run(
        query,
        Findings=findings,
        UpdateTag=aws_update_tag,
        Region=region,
    )


@timeit
def load_inspector_findings(
    neo4j_session: neo4j.Session, findings: List[Dict], region: str,
    aws_update_tag: int,
) -> None:
    for i, findings_batch in enumerate(batch(findings), start=1):
        logger.info(f'Loading batch number {i}')
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
            package.manager = new_package.packageManager,
            package.filepath = new_package.filePath,
            package.fixedinversion = new_package.fixedInVersion,
            package.sourcelayerhash = new_package.sourceLayerHash
        WITH package
        MATCH (finding:AWSInspectorFinding{id: package.findingarn})
        MERGE (finding)-[r:HAS]->(package)
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
    neo4j_session: neo4j.Session, packages: List[Dict], region: str,
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
    run_cleanup_job('aws_import_inspector_cleanup.json', neo4j_session, common_job_parameters)


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
        logger.info(f"Syncing AWS Inspector findings for account {current_aws_account_id} and region {region}")
        findings = get_inspector_findings(boto3_session, region, current_aws_account_id)
        finding_data, package_data = transform_inspector_findings(findings)
        logger.info(f"Loading {len(package_data)} packages")
        load_inspector_packages(neo4j_session, package_data, region, update_tag)
        logger.info(f"Loading {len(finding_data)} findings")
        load_inspector_findings(neo4j_session, finding_data, region, update_tag)
        cleanup(neo4j_session, common_job_parameters)

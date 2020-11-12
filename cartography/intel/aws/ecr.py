import logging
from itertools import chain
from typing import Dict
from typing import Iterator
from typing import List

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ecr_repositories(boto3_session, region) -> List[Dict]:
    logger.debug("Getting ECR repositories for region '%s'.", region)
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('describe_repositories')
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page['repositories'])
    return ecr_repositories


@timeit
@aws_handle_regions
def get_ecr_repository_images(boto3_session, region, repository_name) -> List[Dict]:
    logger.debug("Getting ECR images in repository '%s' for region '%s'.", repository_name, region)
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('list_images')
    ecr_repository_images: List[Dict] = []
    for page in paginator.paginate(repositoryName=repository_name):
        ecr_repository_images.extend(page['imageIds'])
    return ecr_repository_images


@timeit
@aws_handle_regions
def get_ecr_image_scan_findings(boto3_session, region, repository_name, repository_images) -> Iterator[Dict]:
    """
    Returned data shape = [{
        'image_tag': 'TAG',
        'imageDigest': 'sha256:1234',
        'findings_count': {
            'HIGH': 1, 'INFORMATIONAL': 13, 'LOW': 43, 'MEDIUM': 19,
        },
        'findings': [{
            'attributes': [{
                    'key': 'package_version',
                    'value': '1.2.3',
                },{
                    'key': 'package_name',
                    'value': 'some_name',
                }],
            'name': 'CVE-1234-12345',
            'severity': 'HIGH',
            'uri': 'http://example.com',
        }],
        'scan_completed_at': 'abcd',
    }]
    """
    logger.debug("Getting ECR image scan findings in repository '%s' for region '%s'.", repository_name, region)
    client = boto3_session.client('ecr', region_name=region)
    for image in repository_images:
        image_tag = image.get('imageTag', None)

        # We can't call ecr.describe_images() on the image unless it has a tag.
        if image_tag:
            describe_images_resp: Dict = {}
            try:
                describe_images_resp = client.describe_images(
                    repositoryName=repository_name,
                    imageIds=[{
                        'imageDigest': image['imageDigest'],
                        'imageTag': image_tag,
                    }],
                )
            except client.exceptions.ImageNotFoundException:
                logger.warning("Image not found: %s", str(image), exc_info=True)
                continue
            if describe_images_resp['imageDetails'][0].get('imageScanStatus', {}).get('status', None) == "COMPLETE":
                image_vuln = {}
                image_vuln['image_tag'] = image_tag
                if 'imageDigest' in image:
                    image_vuln['imageDigest'] = image['imageDigest']
                else:
                    logger.warning("Image does not have 'imageDigest': %s", str(image))
                    continue
                describe_image_scan_resp = client.describe_image_scan_findings(
                    repositoryName=repository_name,
                    imageId={
                        'imageDigest': image['imageDigest'],
                        'imageTag': image_tag,
                    },
                )
                image_vuln['findings'] = describe_image_scan_resp.get('imageScanFindings', {}).get('findings', [])
                image_vuln['scan_completed_at'] = describe_image_scan_resp.get('imageScanFindings', {}) \
                                                                          .get('imageScanCompletedAt', [])
                image_vuln['findings_count'] = describe_image_scan_resp.get('imageScanFindings', {}) \
                                                                       .get('findingSeverityCounts', [])
                yield image_vuln
        else:
            logger.warning("Image does not have tag: %s", str(image))
            continue


def transform_ecr_scan_finding_attributes(vuln_data) -> Dict:
    """
    Transforms each finding returned from `get_ecr_image_scan_findings()` so that we flatten the  `attributes` list
    to make it easier to load to the graph.
    """
    logger.debug("Transforming ECR image scan findings.")
    for finding in vuln_data.get('findings', []):
        for attrib in finding.get('attributes'):
            if attrib['key'] == 'package_version':
                finding['package_version'] = attrib['value']
            elif attrib['key'] == 'package_name':
                finding['package_name'] = attrib['value']
            elif attrib['key'] == 'CVSS2_SCORE':
                finding['CVSS2_SCORE'] = attrib['value']
    return vuln_data


@timeit
def load_ecr_repositories(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    query = """
    MERGE (repo:ECRRepository{id: {RepositoryArn}})
    ON CREATE SET repo.firstseen = timestamp(), repo.arn = {RepositoryArn}, repo.name = {RepositoryName},
        repo.region = {Region}, repo.created_at = {CreatedAt}
    SET repo.lastupdated = {aws_update_tag}, repo.uri = {RepositoryUri}
    WITH repo
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(repo)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    logger.debug("Loading ECR repositories for region '%s' into graph.", region)
    for repo in data:
        neo4j_session.run(
            query,
            RepositoryArn=repo['repositoryArn'],
            RepositoryName=repo['repositoryName'],
            RepositoryUri=repo['repositoryUri'],
            CreatedAt=str(repo['createdAt']),
            Region=region,
            aws_update_tag=aws_update_tag,
            AWS_ACCOUNT_ID=current_aws_account_id,
        ).consume()  # See issue #440


@timeit
def load_ecr_repository_images(neo4j_session, repo_data, region, aws_update_tag):
    query = """
    MERGE (repo_image:ECRRepositoryImage{id: {RepositoryImageUri}})
    ON CREATE SET repo_image.firstseen = timestamp()
    SET repo_image.lastupdated = {aws_update_tag}, repo_image.tag = {ImageTag},
        repo_image.uri = {RepositoryImageUri}
    WITH repo_image

    MERGE (image:ECRImage{id: {ImageDigest}})
    ON CREATE SET image.firstseen = timestamp(), image.digest = {ImageDigest}
    SET image.lastupdated = {aws_update_tag},
    image.region = {Region}
    WITH repo_image, image
    MERGE (repo_image)-[r1:IMAGE]->(image)
    ON CREATE SET r1.firstseen = timestamp()
    SET r1.lastupdated = {aws_update_tag}
    WITH repo_image

    MATCH (repo:ECRRepository{uri: {RepositoryUri}})
    MERGE (repo)-[r2:REPO_IMAGE]->(repo_image)
    ON CREATE SET r2.firstseen = timestamp()
    SET r2.lastupdated = {aws_update_tag}
    """
    logger.debug("Loading ECR repository images for region '%s' into graph.", region)
    for repo_uri, repo_images in repo_data.items():
        for repo_image in repo_images:
            image_tag = repo_image.get('imageTag', '')
            # TODO this assumes image tags and uris are immutable
            repo_image_uri = f"{repo_uri}:{image_tag}" if image_tag else repo_uri
            neo4j_session.run(
                query,
                RepositoryImageUri=repo_image_uri,
                ImageDigest=repo_image['imageDigest'],
                ImageTag=image_tag,
                RepositoryUri=repo_uri,
                aws_update_tag=aws_update_tag,
                Region=region,
            ).consume()  # See issue #440


@timeit
def load_ecr_image_scan_findings(neo4j_session, data, aws_update_tag):
    """
    Creates the path (:Risk:CVE:ECRScanFinding)-[:AFFECTS]->(:Package)-[:DEPLOYED]->(:ECRImage)
    :param neo4j_session: The Neo4j session object
    :param data: A dict that has been run through transform_ecr_scan_finding_attributes().
    :param aws_update_tag: The AWS update tag
    """
    query = """
    UNWIND {Risks} as risk
        MATCH (image:ECRImage{id: {ImageDigest}})
        MERGE (pkg:Package{id: risk.package_version + "|" + risk.package_name})
        ON CREATE SET pkg.firstseen = timestamp(),
        pkg.name = risk.package_name,
        pkg.version = risk.package_version
        SET pkg.lastupdated = {aws_update_tag}
        WITH image, risk, pkg

        MERGE (pkg)-[r1:DEPLOYED]->(image)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = {aws_update_tag}
        WITH pkg, risk

        MERGE (r:Risk:CVE:ECRScanFinding{id: risk.name})
        ON CREATE SET r.firstseen = timestamp(),
        r.name = risk.name,
        r.severity = risk.severity
        SET r.lastupdated = {aws_update_tag},
        r.uri = risk.uri,
        r.cvss2_score = risk.CVSS2_SCORE

        MERGE (r)-[a:AFFECTS]->(pkg)
        ON CREATE SET a.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
        """
    logger.debug("Loading ECR image scan findings into graph.")
    neo4j_session.run(
        query,
        Risks=data['findings'],
        ImageDigest=data['imageDigest'],
        aws_update_tag=aws_update_tag,
    ).consume()  # See issue #440


def cleanup(neo4j_session, common_job_parameters):
    logger.debug("Running ECR cleanup job.")
    run_cleanup_job('aws_import_ecr_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        image_data = {}
        images_with_vulns = iter(())
        repositories = get_ecr_repositories(boto3_session, region)
        for repo in repositories:
            repo_image_obj = get_ecr_repository_images(boto3_session, region, repo['repositoryName'])
            image_data[repo['repositoryUri']] = repo_image_obj
            image_vulns = get_ecr_image_scan_findings(
                boto3_session, region, repo['repositoryName'], repo_image_obj,
            )
            transformed_attrs = (
                transform_ecr_scan_finding_attributes(v)
                for v in image_vulns
            ) if image_vulns else iter(())
            images_with_vulns = chain(images_with_vulns, transformed_attrs)

        load_ecr_repositories(neo4j_session, repositories, region, current_aws_account_id, aws_update_tag)
        load_ecr_repository_images(neo4j_session, image_data, region, aws_update_tag)
        for image_vuln_data in images_with_vulns:
            load_ecr_image_scan_findings(neo4j_session, image_vuln_data, aws_update_tag)
    cleanup(neo4j_session, common_job_parameters)

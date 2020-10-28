import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_ecr_repositories(boto3_session, region):
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('describe_repositories')
    ecr_repositories = []
    for page in paginator.paginate():
        ecr_repositories.extend(page['repositories'])
    return ecr_repositories


def get_ecr_repository_images(boto3_session, region, repository_name):
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('list_images')
    ecr_repository_images = []
    for page in paginator.paginate(repositoryName=repository_name):
        ecr_repository_images.extend(page['imageIds'])
    return ecr_repository_images


def get_repository_images_vulns(boto3_session, region, repository_name, repository_images):
    client = boto3_session.client('ecr', region_name=region)
    image_vuln_dict = {}
    for image in repository_images:
        image_tag = image.get('imageTag', None)
        if image_tag not in image_vuln_dict and image_tag != None:
            image_vuln_dict[image_tag] = {}
            response = client.describe_images(repositoryName=repository_name,
                imageIds=[{'imageDigest':image['imageDigest'], 'imageTag': image['imageTag']}])

            if response['imageDetails'][0].get('imageScanStatus', {}).get('status', None) == "COMPLETE":
                response = client.describe_image_scan_findings(repositoryName=repository_name,
                    imageId={'imageDigest':image['imageDigest'], 'imageTag': image['imageTag']})
                image_vuln_dict[image_tag]['findings'] = response.get('imageScanFindings', {}).get('findings', [])
                image_vuln_dict[image_tag]['scan_completed_at'] = response.get('imageScanFindings', {}).get('imageScanCompletedAt', [])
                image_vuln_dict[image_tag]['findings_count'] =response.get('imageScanFindings', {}).get('findingSeverityCounts', [])

    return image_vuln_dict


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
        )


def load_ecr_repository_images(neo4j_session, data, region, aws_update_tag):
    query = """
    MERGE (repo_image:ECRRepositoryImage{id: {RepositoryImageUri}})
    ON CREATE SET repo_image.firstseen = timestamp()
    SET repo_image.lastupdated = {aws_update_tag}, repo_image.tag = {ImageTag},
        repo_image.uri = {RepositoryImageUri}
    WITH repo_image
    MERGE (image:ECRImage{id: {ImageDigest}})
    ON CREATE SET image.firstseen = timestamp(), image.digest = {ImageDigest}
    SET image.last_updated = {aws_update_tag}
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

    for repo_uri, repo_images in data.items():
        for repo_image in repo_images:
            image_tag = repo_image.get('imageTag', '')
            repo_image_uri = f"{repo_uri}:{image_tag}"  # TODO this assumes image tags and uris are immutable
            neo4j_session.run(
                query,
                RepositoryImageUri=repo_image_uri,
                ImageDigest=repo_image['imageDigest'],
                ImageTag=image_tag,
                RepositoryUri=repo_uri,
                aws_update_tag=aws_update_tag,
            )


def load_ecr_image_vulns(neo4j_session, data, region, aws_update_tag):
    query = """
    MERGE (repo_image:ECRRepositoryImage{id: {RepositoryImageUri}})
    ON CREATE SET repo_image.firstseen = timestamp()
    SET repo_image.lastupdated = {aws_update_tag}, repo_image.tag = {ImageTag},
        repo_image.uri = {RepositoryImageUri}
    WITH repo_image
    MERGE (image:ECRImage{id: {ImageDigest}})
    ON CREATE SET image.firstseen = timestamp(), image.digest = {ImageDigest}
    SET image.last_updated = {aws_update_tag}
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

    for image_uri, image_vulns_data in data.items():
        if image_vulns_data != {}:
            for finding in image_vulns_data['findings']:
                repo_image_uri = image_uri  # TODO this assumes image tags and uris are immutable
                neo4j_session.run(
                    query,
                    RepositoryImageUri=repo_image_uri,
                    ImageDigest=repo_image['imageDigest'],
                    ImageTag=repo_image['imageTag'],
                    RepositoryUri=repo_uri,
                    aws_update_tag=aws_update_tag,
                )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ecr_cleanup.json', neo4j_session, common_job_parameters)


def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        repository_data = get_ecr_repositories(boto3_session, region)
        image_data = {}
        image_vulns = {}
        for repo in repository_data:
            image_data[repo['repositoryUri']] = get_ecr_repository_images(boto3_session, region, repo['repositoryName'])
            image_vulns = get_repository_images_vulns(
                boto3_session, region, repo['repositoryName'], image_data[repo['repositoryUri']])
        load_ecr_repositories(neo4j_session, repository_data, region, current_aws_account_id, aws_update_tag)
        load_ecr_repository_images(neo4j_session, image_data, region, aws_update_tag)
        #load_ecr_image_vulns(neo4j_session, image_vulns, region, aws_update_tag)
    cleanup(neo4j_session, common_job_parameters)

import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_ecr_repositories(boto3_session, region):
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('describe_repositories')
    ecr_repositories = []
    for page in paginator.paginate():
        ecr_repositories.extend(page['repositories'])
    return {'repositories': ecr_repositories}


def get_ecr_repository_images(boto3_session, region, repository_name):
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('list_images')
    ecr_repository_images = []
    for page in paginator.paginate(repositoryName=repository_name):
        ecr_repository_images.extend(page['imageIds'])
    return ecr_repository_images


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

    for repo in data['repositories']:
        neo4j_session.run(
            query,
            RepositoryArn=repo['repositoryArn'],
            RepositoryName=repo['repositoryName'],
            RepositoryUri=repo['repositoryUri'],
            CreatedAt=repo['createdAt'],  # TODO this is documented as a datetime but testing indicates it's unix time
            Region=region,
            aws_update_tag=aws_update_tag,
            AWS_ACCOUNT_ID=current_aws_account_id,
        )


def load_ecr_images(neo4j_session, data, region, aws_update_tag):
    query = """
    MERGE (image:ECRImage{id: {ImageDigest}})
    ON CREATE SET image.firstseen = timestamp(), image.digest = {ImageDigest}
    SET image.lastupdated = {aws_update_tag}, image.tag = {ImageTag}
    WITH image
    MATCH (repo:ECRRepository{id: {RepositoryArn}})
    MERGE (repo)-[r:IMAGE]->(image)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    for repo_arn, repo_images in data.items():
        for repo_image in repo_images:
            neo4j_session.run(
                query,
                RepositoryArn=repo_arn,
                ImageDigest=repo_image['imageDigest'],
                ImageTag=repo_image['imageTag'],
                aws_update_tag=aws_update_tag,
            )


def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ecr_cleanup.json', neo4j_session, common_job_parameters)


def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        repository_data = get_ecr_repositories(boto3_session, region)
        image_data = {}
        for repo in repository_data:
            image_data[repo['repositoryArn']] = get_ecr_repository_images(boto3_session, region, repo['repositoryName'])
        load_ecr_repositories(neo4j_session, repository_data, region, current_aws_account_id, aws_update_tag)
        load_ecr_images(neo4j_session, image_data, region, current_aws_account_id, aws_update_tag)
    cleanup(neo4j_session, common_job_parameters)

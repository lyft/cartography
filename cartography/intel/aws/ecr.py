import logging
from typing import Dict
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
def transform_ecr_repository_images(repo_data):
    """
    Ensure that we only load ECRImage nodes to the graph if they have a defined imageDigest field.
    """
    repo_images_list = []
    for repo_uri, repo_images in repo_data.items():
        filtered_imgs = []
        for img in repo_images:
            if 'imageDigest' in img and img['imageDigest']:
                filtered_imgs.append(img)
            else:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get('imageTag'),
                )

        repo_images_list.append({
            'repo_uri': repo_uri,
            'repo_images': filtered_imgs,
        })
    return repo_images_list


@timeit
def load_ecr_repository_images(neo4j_session, repo_images_list, region, aws_update_tag):
    query = """
    UNWIND {RepoList} as repo_item
        UNWIND repo_item.repo_images as repo_img
            MERGE (ri:ECRRepositoryImage{id: repo_item.repo_uri + COALESCE(":" + repo_img.imageTag, '')})
            ON CREATE SET ri.firstseen = timestamp()
            SET ri.lastupdated = {aws_update_tag},
                ri.tag = repo_img.imageTag,
                ri.uri = repo_item.repo_uri + COALESCE(":" + repo_img.imageTag, '')
            WITH ri, repo_img, repo_item

            MERGE (img:ECRImage{id: repo_img.imageDigest})
            ON CREATE SET img.firstseen = timestamp(),
                img.digest = repo_img.imageDigest
            SET img.lastupdated = {aws_update_tag},
                img.region = {Region}
            WITH ri, img, repo_item

            MERGE (ri)-[r1:IMAGE]->(img)
            ON CREATE SET r1.firstseen = timestamp()
            SET r1.lastupdated = {aws_update_tag}
            WITH ri, repo_item

            MATCH (repo:ECRRepository{uri: repo_item.repo_uri})
            MERGE (repo)-[r2:REPO_IMAGE]->(ri)
            ON CREATE SET r2.firstseen = timestamp()
            SET r2.lastupdated = {aws_update_tag}
    """
    logger.debug("Loading ECR repository images for region '%s' into graph.", region)
    neo4j_session.run(
        query,
        RepoList=repo_images_list,
        aws_update_tag=aws_update_tag,
        Region=region,
    ).consume()  # See issue #440


@timeit
def cleanup(neo4j_session, common_job_parameters):
    logger.debug("Running ECR cleanup job.")
    run_cleanup_job('aws_import_ecr_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag, common_job_parameters):
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        image_data = {}
        repositories = get_ecr_repositories(boto3_session, region)
        for repo in repositories:
            repo_image_obj = get_ecr_repository_images(boto3_session, region, repo['repositoryName'])
            image_data[repo['repositoryUri']] = repo_image_obj
        load_ecr_repositories(neo4j_session, repositories, region, current_aws_account_id, aws_update_tag)
        repo_images_list = transform_ecr_repository_images(image_data)
        load_ecr_repository_images(neo4j_session, repo_images_list, region, aws_update_tag)
    cleanup(neo4j_session, common_job_parameters)

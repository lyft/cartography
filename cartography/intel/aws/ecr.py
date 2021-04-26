import logging
from typing import Dict
from typing import List
from datetime import datetime
import pytz

import boto3
import neo4j
import neomodel

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


# class CartographyNode(neomodel.StructuredNode):
#     # neomodel.DateTimeProperty(
#     #     default=lambda: datetime.now(pytz.utc)
#     # )
#     firstseen = neomodel.DateTimeProperty()
#     lastupdated = neomodel.IntegerProperty()


class CartographyRel(neomodel.StructuredRel):
    firstseen = neomodel.DateTimeProperty(
        default=lambda: datetime.now(pytz.utc)
    )
    lastupdated = neomodel.IntegerProperty()


class AWSAccount(neomodel.StructuredNode):
    #id = neomodel.StringProperty(unique_index=True)
    id = neomodel.StringProperty()
    name = neomodel.StringProperty()
    firstseen = neomodel.DateTimeProperty()
    lastupdated = neomodel.IntegerProperty()


class ECRImage(neomodel.StructuredNode):
    #id = neomodel.StringProperty(unique_index=True)
    id = neomodel.StringProperty()
    digest = neomodel.StringProperty() # TODO check this
    region = neomodel.StringProperty()
    firstseen = neomodel.DateTimeProperty()
    lastupdated = neomodel.IntegerProperty()


class ECRRepositoryImage(neomodel.StructuredNode):
    # id = neomodel.StringProperty(unique_index=True)
    # tag = neomodel.StringProperty(index=True) # TODO check this
    # uri = neomodel.StringProperty(index=True)
    id = neomodel.StringProperty()
    tag = neomodel.StringProperty() # TODO check this
    uri = neomodel.StringProperty()
    firstseen = neomodel.DateTimeProperty()
    lastupdated = neomodel.IntegerProperty()

    ecr_image = neomodel.RelationshipTo(ECRImage, 'IMAGE')


class ECRRepository(neomodel.StructuredNode):
    # id = neomodel.StringProperty(unique_index=True)
    # arn = neomodel.StringProperty(unique_index=True)
    id = neomodel.StringProperty()
    arn = neomodel.StringProperty()
    name = neomodel.StringProperty()
    region = neomodel.StringProperty()
    created_at = neomodel.DateTimeProperty()
    # uri = neomodel.StringProperty(index=True)
    uri = neomodel.StringProperty()
    firstseen = neomodel.DateTimeProperty()
    lastupdated = neomodel.IntegerProperty()

    account = neomodel.RelationshipFrom(AWSAccount, "RESOURCE")
    ecr_repository_image = neomodel.RelationshipTo(ECRRepositoryImage, 'REPO_IMAGE')


@timeit
@aws_handle_regions
def get_ecr_repositories(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    logger.info("Getting ECR repositories for region '%s'.", region)
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('describe_repositories')
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page['repositories'])
    return ecr_repositories


@timeit
@aws_handle_regions
def get_ecr_repository_images(boto3_session: boto3.session.Session, region: str, repository_name: str) -> List[Dict]:
    logger.debug("Getting ECR images in repository '%s' for region '%s'.", repository_name, region)
    client = boto3_session.client('ecr', region_name=region)
    paginator = client.get_paginator('list_images')
    ecr_repository_images: List[Dict] = []
    for page in paginator.paginate(repositoryName=repository_name):
        ecr_repository_images.extend(page['imageIds'])
    return ecr_repository_images


@timeit
def load_ecr_repositories(
    neo4j_session: neo4j.Session, repos: List[Dict], region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(repos)} ECR repositories for region {region} into graph.")
    try:
        aws_account = AWSAccount.nodes.get(id=current_aws_account_id)
    except neomodel.exceptions.ModelDefinitionMismatch as e:
        print(e)
        raise
    for repo in repos:
        print(repo)
        ecr_repo = ECRRepository(
            id=repo['repositoryArn'],
            arn=repo['repositoryArn'],
            name=repo['repositoryName'],
            created_at=datetime.now(),
            region=region,
            uri=repo['repositoryUri'],
            firstseen=datetime.now(),
            lastupdated=aws_update_tag,
        )
        ecr_repo.save()
        ecr_repo.refresh()
        ecr_repo.account.connect(aws_account)


@timeit
def transform_ecr_repository_images(repo_data: Dict) -> List[Dict]:
    """
    Ensure that we only load ECRImage nodes to the graph if they have a defined imageDigest field.
    """
    repo_images_list = []
    for repo_uri, repo_images in repo_data.items():
        for img in repo_images:
            if 'imageDigest' in img and img['imageDigest']:
                img['repo_uri'] = repo_uri
                repo_images_list.append(img)
            else:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get('imageTag'),
                )

    return repo_images_list


@timeit
def load_ecr_repository_images(
        neo4j_session: neo4j.Session, repo_images_list: List[Dict], region: str, aws_update_tag: int,
) -> None:
    for repo_img in repo_images_list:
        repo_img_node = ECRRepositoryImage(
            id=f"{repo_img['repo_uri']}:{repo_img['imageTag']}" if repo_img.get('imageTag') else repo_img['repo_uri'],
            tag=repo_img['imageTag'],
            uri=f"{repo_img['repo_uri']}:{repo_img['imageTag']}" if repo_img.get('imageTag') else repo_img['repo_uri'],
            lastupdated=aws_update_tag,
        )
        repo_img_node.save()
        repo_node = ECRRepository.nodes.get(uri=repo_img['repo_uri'])
        repo_node.ecr_repository_image.connect(repo_img_node)

        img_node = ECRImage(
            id=repo_img['imageDigest'],
            digest=repo_img['imageDigest'],
            lastupdated=aws_update_tag,
            region=region,
        )
        img_node.save()
        repo_img_node.ecr_image.connect(img_node)


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running ECR cleanup job.")
    run_cleanup_job('aws_import_ecr_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing ECR for region '%s' in account '%s'.", region, current_aws_account_id)
        image_data = {}
        repositories = get_ecr_repositories(boto3_session, region)
        for repo in repositories:
            repo_image_obj = get_ecr_repository_images(boto3_session, region, repo['repositoryName'])
            image_data[repo['repositoryUri']] = repo_image_obj
        load_ecr_repositories(neo4j_session, repositories, region, current_aws_account_id, update_tag)
        repo_images_list = transform_ecr_repository_images(image_data)
        load_ecr_repository_images(neo4j_session, repo_images_list, region, update_tag)
    cleanup(neo4j_session, common_job_parameters)

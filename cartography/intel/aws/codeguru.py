import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_repository_associations(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('codeguru-reviewer', region_name=region)
    paginator = client.get_paginator('list_repository_associations')
    associations: List[Any] = []
    for page in paginator.paginate():
        associations.extend(page.get('RepositoryAssociationSummaries', []))

    return associations


@timeit
def get_association_names(associations: List[Dict]) -> List[str]:
    names: List[Any] = []
    for assoc in associations:
        names.append(assoc['Name'])

    return names


@timeit
@aws_handle_regions
def get_recommendation_feedbacks(
    boto3_session: boto3.session.Session,
    region: str, code_reviews: List[Dict],
) -> List[Dict[Any, Any]]:
    client = boto3_session.client('codeguru-reviewer', region_name=region)

    queues: List[Dict] = []
    for cr in code_reviews:
        response = client.list_recommendation_feedback(CodeReviewArn=cr['CodeReviewArn'])
        for queue in response['RecommendationFeedbackSummaries']:
            queue['Reactions'] = queue['Reactions'][0]
            queue['RecommendationId'] = queue['RecommendationId']
            queues.append(queue)

    return queues


@timeit
@aws_handle_regions
def get_code_reviews(boto3_session: boto3.session.Session, region: str, association_names: List[str]) -> List[Dict]:
    client = boto3_session.client('codeguru-reviewer', region_name=region)
    response = client.list_code_reviews(States=['Completed'], Type='PullRequest', RepositoryNames=association_names)
    return response['CodeReviewSummaries']


@timeit
@aws_handle_regions
def get_recommendations(
    boto3_session: boto3.session.Session,
    region: str,
    code_reviews: List[Dict],
) -> List[Dict[Any, Any]]:
    client = boto3_session.client('codeguru-reviewer', region_name=region)

    queues: List[Dict] = []
    for cr in code_reviews:
        response = client.list_recommendations(CodeReviewArn=cr['CodeReviewArn'])
        for queue in response['RecommendationSummaries']:
            queue['CodeReviewArn'] = cr['CodeReviewArn']
            queues.append(queue)

    return queues


@timeit
def load_repository_associations(
    neo4j_session: neo4j.Session,
    data: list,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    cypher = """
    UNWIND {Repos} AS repo
        MERGE (cga:CodeguruAssociation{id: repo.AssociationArn})
        ON CREATE SET cga.firstseen = timestamp()
        SET
             cga.associationid = repo.AssociationId,
             cga.name = repo.Name,
             cga.owner = repo.Owner,
             cga.providertype = repo.ProviderType,
             cga.state = repo.State,
             cga.lastupdated = {aws_update_tag}
        WITH cga
        MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
        MERGE (owner)-[r:RESOURCE]->(cga)
        ON CREATE SET cga.firstseen = timestamp()
        SET cga.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        cypher,
        Repos=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_code_reviews(
    neo4j_session: neo4j.Session,
    data: list,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    cypher = """
    UNWIND {Repos} AS repo
        MERGE (cgc:CodeguruCodereview{id: repo.CodeReviewArn})
        ON CREATE SET cgc.firstseen = timestamp()
        SET
             cgc.associationarn = repo.AssociationArn,
             cgc.name = repo.Name,
             cgc.owner = repo.Owner,
             cgc.providertype = repo.ProviderType,
             cgc.pullrequestId = repo.PullRequestId,
             cgc.repositoryname = repo.RepositoryName,
             cgc.state = repo.State,
             cgc.type = repo.Type,
             cgc.lastupdated = {aws_update_tag}
        WITH cgc,repo
        MATCH (cga:CodeguruAssociation{id: repo.AssociationArn})
        MERGE (cga)-[r:HAS_CODEREVIEW]->(cgc)
        ON CREATE SET cgc.firstseen = timestamp()
        SET cgc.lastupdated = {aws_update_tag}
    """

    for i in range(len(data)):
        data[i]['AssociationArn'] = data[i]['CodeReviewArn'].split(':code-review:')[0]

    neo4j_session.run(
        cypher,
        Repos=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_recommendations(
    neo4j_session: neo4j.Session,
    data: list,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    cypher = """
    UNWIND {Repos} AS repo
        MERGE (cgr:CodeguruRecommendation{id: repo.RecommendationId + COALESCE(":" + repo.CodeReviewArn, '')})
        ON CREATE SET cgr.firstseen = timestamp()
        SET
             cgr.codereviewarn = repo.CodeReviewArn,
             cgr.description = repo.Description,
             cgr.filepath = repo.FilePath,
             cgr.recommendationcategory = repo.RecommendationCategory,
             cgr.severity = repo.Severity,
             cgr.recommendationid = repo.RecommendationId,
             cgr.startline = repo.StartLine,
             cgr.endLine = repo.EndLine,
             cgr.lastupdated = {aws_update_tag}
        WITH cgr,repo
        MATCH (cgc:CodeguruCodereview{id: repo.CodeReviewArn})
        MERGE (cgc)-[r:HAS_RECOMMENDATION]->(cgr)
        ON CREATE SET cgr.firstseen = timestamp()
        SET cgr.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        cypher,
        Repos=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_recommendation_feedbacks(
    neo4j_session: neo4j.Session,
    data: list,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    cypher = """
    UNWIND {Repos} AS repo
        MERGE (crf:CodeguruRecommendationFeedback{id: repo.RecommendationId})
        ON CREATE SET crf.firstseen = timestamp()
        SET
             crf.reactions = repo.Reactions,
             crf.lastupdated = {aws_update_tag}
        WITH crf,repo
        MATCH (cgr:CodeguruRecommendation{id: repo.RecommendationId})
        MERGE (cgr)-[r:HAS_RECOMMENDATION_FEEDBACK]->(crf)
        ON CREATE SET crf.firstseen = timestamp()
        SET crf.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        cypher,
        Repos=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_codeguru_associations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_codeguru_associations_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_codeguru_codereviews(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_codeguru_codereviews_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    regions = boto3_session.get_available_regions('codeguru-reviewer')

    for region in regions:
        logger.info("Syncing CodeGuru for region '%s' in account '%s'.", region, current_aws_account_id)
        associations = get_repository_associations(boto3_session, region)
        if len(associations) == 0:
            continue
        logger.info(associations)
        association_names = get_association_names(associations)

        load_repository_associations(neo4j_session, associations, region, current_aws_account_id, update_tag)

        code_reviews = get_code_reviews(boto3_session, region, association_names)
        load_code_reviews(neo4j_session, code_reviews, region, current_aws_account_id, update_tag)

        recommendations = get_recommendations(boto3_session, region, code_reviews)
        load_recommendations(neo4j_session, recommendations, region, current_aws_account_id, update_tag)

        recommendation_feedbacks = get_recommendation_feedbacks(boto3_session, region, code_reviews)
        load_recommendation_feedbacks(
            neo4j_session,
            recommendation_feedbacks,
            region,
            current_aws_account_id,
            update_tag,
        )

        cleanup_codeguru_codereviews(neo4j_session, common_job_parameters)
        cleanup_codeguru_associations(neo4j_session, common_job_parameters)

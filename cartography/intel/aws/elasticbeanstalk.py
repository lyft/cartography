import json
import logging
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.stats import get_stats_client
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def get_elasticbeanstalk_applications(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3.client('elasticbeanstalk')

    applications = []

    try:

        client_describe_applications = client.describe_applications()

        applications = client_describe_applications['Applications']

        for application in applications:
            application['EnvironmentsList'] = get_application_environments(
                boto3_session,
                application['ApplicationName'],
            )
            application['VersionsList'] = get_application_versions(boto3_session, application['ApplicationName'])

    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not run ElasticBeanStalk - Client Error due to boto3 error %s: %s. Skipping.",
            e.response['Error']['Code'],
            e.response['Error']['Message'],
        )

    return applications


@timeit
def get_application_environments(boto3_session: boto3.session.Session, application_name: str) -> List[Dict]:
    client = boto3.client('elasticbeanstalk')
    paginator = client.get_paginator('describe_environments')

    enviroments = []

    for page in paginator.paginate(ApplicationName=application_name):
        for environment in page['Environments']:
            env_resources = client.describe_environment_resources(EnvironmentId=environment['EnvironmentId'])
            environment['EnvironmentResources'] = env_resources['EnvironmentResources']

            enviroments.append(environment)

    return enviroments


@timeit
def get_application_versions(boto3_session: boto3.session.Session, application_name: str) -> List[Dict]:
    client = boto3.client('elasticbeanstalk')
    paginator = client.get_paginator('describe_application_versions')

    enviroments = []

    for page in paginator.paginate(ApplicationName=application_name):
        for environment in page['ApplicationVersions']:
            enviroments.append(environment)

    return enviroments


@timeit
def load_elasticbeanstalk_enviroments(
        neo4j_session: neo4j.Session,
        distribution_arn: str,
        environments: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_definitions = """
         MERGE (d:ElasticBeanStalkEnvironment{id: $environment.EnvironmentArn})
         ON CREATE SET d.firstseen = timestamp()
         SET
            d.arn = $environment.EnvironmentArn,
            d.name = $environment.EnvironmentName,
            d.id = $environment.EnvironmentId,
            d.application_name = $environment.ApplicationName,
            d.version_label = $environment.VersionLabel,
            d.solution_stack_name = $environment.SolutionStackName,
            d.platform_arn = $environment.PlatformArn,
            d.template_name = $environment.TemplateName,
            d.description = $environment.Description,
            d.endpoint_URL = $environment.EndpointURL,
            d.cname = $environment.CNAME,
            d.date_created = $environment.DateCreated,
            d.status = $environment.Status,
            d.abortable_operation_in_progress = $environment.AbortableOperationInProgress,
            d.health = $environment.Health,
            d.health_status = $environment.HealthStatus,
            d.operations_role = $environment.OperationsRole,
            d.tier = $environment.Tier,
            d.resources = $environment.Resources,
            d.environment_links = $environment.EnvironmentLinks,
            d.environment_resources = $environment.EnvironmentResources2,
            d.lastupdated = $aws_update_tag
         WITH d
         MATCH (td:ElasticBeanStalkApplication{arn: $distribution_arn})
         MERGE (td)-[r:HAS_ENVIRONMENT]->(d)
         ON CREATE SET r.firstseen = timestamp()
         SET r.lastupdated = $aws_update_tag
         WITH d
         MATCH(tv:ElasticBeanStalkVersion{version_label: $environment.VersionLabel})
         MERGE (d)-[v:IS_RUNNING_VERSION]->(tv)
         ON CREATE SET v.firstseen = timestamp()
         SET v.lastupdated = $aws_update_tag
         """

    ingest_autoscalinggroup = """
        UNWIND $list as l
        MERGE (envresource:AutoScalingGroup{name: l.Name})
        ON CREATE SET envresource.firstseen = timestamp()
        SET envresource.lastupdated = $aws_update_tag
        WITH envresource
        MATCH (environment:ElasticBeanStalkEnvironment{arn: $environment_arn})
        MERGE (environment)-[r:HAS_ENVIRONMENT_RESOURCE]->(envresource)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """

    ingest_launchconfigurations = """
        UNWIND $list as l
        MERGE (envresource:LaunchConfiguration{name: l.Name})
        ON CREATE SET envresource.firstseen = timestamp()
        SET envresource.lastupdated = $aws_update_tag
        WITH envresource
        MATCH (environment:ElasticBeanStalkEnvironment{arn: $environment_arn})
        MERGE (environment)-[r:HAS_ENVIRONMENT_RESOURCE]->(envresource)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """

    ingest_instance = """
            UNWIND $list as l
            MERGE (envresource:EC2Instance{id: l.Id})
            ON CREATE SET envresource.firstseen = timestamp()
            SET envresource.lastupdated = $aws_update_tag
            WITH envresource
            MATCH (environment:ElasticBeanStalkEnvironment{arn: $environment_arn})
            MERGE (environment)-[r:HAS_ENVIRONMENT_RESOURCE]->(envresource)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $aws_update_tag
            """

    ingest_launchtemplates = """
        UNWIND $list as l
        MERGE (envresource:LaunchTemplate{name: l.Name})
        ON CREATE SET envresource.firstseen = timestamp()
        SET envresource.lastupdated = $aws_update_tag
        WITH envresource
        MATCH (environment:ElasticBeanStalkEnvironment{arn: $environment_arn})
        MERGE (environment)-[r:HAS_ENVIRONMENT_RESOURCE]->(envresource)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """

    ingest_loadbalancers = """
        UNWIND $list as l
        MERGE (envresource:LoadBalancer{name: l.Name})
        ON CREATE SET envresource.firstseen = timestamp()
        SET envresource.lastupdated = $aws_update_tag
        WITH envresource
        MATCH (environment:ElasticBeanStalkEnvironment{arn: $environment_arn})
        MERGE (environment)-[r:HAS_ENVIRONMENT_RESOURCE]->(envresource)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """

    for environment in environments:
        environment["DateCreated"] = dict_date_to_epoch(environment, 'DateCreated')

        if environment['AbortableOperationInProgress']:
            environment['AbortableOperationInProgress'] = "true"
        else:
            environment['AbortableOperationInProgress'] = "false"

        if environment.get('Tier'):
            environment["Tier"] = json.dumps(environment["Tier"])

        if environment.get('Resources'):
            environment["Resources"] = json.dumps(environment["Resources"])

        if environment.get('EnvironmentLinks'):
            environment["EnvironmentLinks"] = json.dumps(environment["EnvironmentLinks"])

        if environment.get('EnvironmentResources'):
            environment["EnvironmentResources2"] = json.dumps(environment["EnvironmentResources"])

        neo4j_session.run(
            ingest_definitions,
            distribution_arn=distribution_arn,
            environment=environment,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_autoscalinggroup,
            list=environment['EnvironmentResources']['AutoScalingGroups'],
            environment_arn=environment['EnvironmentArn'],
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_instance,
            list=environment['EnvironmentResources']['Instances'],
            environment_arn=environment['EnvironmentArn'],
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_launchconfigurations,
            list=environment['EnvironmentResources']['LaunchConfigurations'],
            environment_arn=environment['EnvironmentArn'],
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_launchtemplates,
            list=environment['EnvironmentResources']['LaunchTemplates'],
            environment_arn=environment['EnvironmentArn'],
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_loadbalancers,
            list=environment['EnvironmentResources']['LoadBalancers'],
            environment_arn=environment['EnvironmentArn'],
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_elasticbeanstalk_versions(
        neo4j_session: neo4j.Session,
        distribution_arn: str,
        versions: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_definitions = """
         MERGE (d:ElasticBeanStalkVersion{id: $version.ApplicationVersionArn})
         ON CREATE SET d.firstseen = timestamp()
         SET
            d.arn = $version.ApplicationVersionArn,
             d.application_name = $version.ApplicationName,
             d.description = $version.Description,
             d.version_label = $version.VersionLabel,
             d.build_arn = $version.BuildArn,
             d.date_created = $version.DateCreated,
             d.status = $version.Status,
             d.source_build_information = $version.SourceBuildInformation,
             d.source_bundle = $version.SourceBundle2,
             d.lastupdated = $aws_update_tag
         WITH d
         MATCH (td:ElasticBeanStalkApplication{arn: $distribution_arn})
         MERGE (td)-[r:HAS_VERSION]->(d)
         ON CREATE SET r.firstseen = timestamp()
         SET r.lastupdated = $aws_update_tag
         """

    ingest_s3bucket = """
            MERGE (s3:S3Bucket{name: $s3_name})
            ON CREATE SET s3.firstseen = timestamp()
            SET s3.lastupdated = $aws_update_tag
            WITH s3
            MATCH (version:ElasticBeanStalkVersion{arn: $version_arn})
            MERGE (version)-[r:HAS_SOURCE]->(s3)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $aws_update_tag
            """

    for version in versions:
        version["DateCreated"] = dict_date_to_epoch(version, 'DateCreated')

        if version.get('SourceBundle'):
            version["SourceBundle2"] = json.dumps(version["SourceBundle"])

        if version.get('SourceBuildInformation'):
            version["SourceBuildInformation"] = json.dumps(version["SourceBuildInformation"])

        neo4j_session.run(
            ingest_definitions,
            distribution_arn=distribution_arn,
            version=version,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        neo4j_session.run(
            ingest_s3bucket,
            s3_name=version["SourceBundle"]['S3Bucket'],
            version_arn=version['ApplicationVersionArn'],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_elasticbeanstalk_applications(
        neo4j_session: neo4j.Session,
        data: List[Dict],
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    ingest_distribution = """
             MERGE (d:ElasticBeanStalkApplication{id: $distribution.ApplicationArn})
             ON CREATE SET d.firstseen = timestamp()
             SET d.arn = $distribution.ApplicationArn,
                 d.name = $distribution.ApplicationName,
                 d.domain_name = $distribution.DomainName,
                 d.description = $distribution.Description,
                 d.date_created = $distribution.DateCreated,
                 d.configuration_templates = $distribution.ConfigurationTemplates,
                 d.resource_lifecycle_config = $distribution.ResourceLifecycleConfig,
                 d.versions = $distribution.Versions,
                 d.lastupdated = $aws_update_tag
             WITH d
             MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
             MERGE (owner)-[r:RESOURCE]->(d)
             ON CREATE SET r.firstseen = timestamp()
             SET r.lastupdated = $aws_update_tag
         """

    for application in data:
        application["DateCreated"] = dict_date_to_epoch(application, 'DateCreated')

        # ask if we want to add this in the distribution since we already have lastupdated
        application["DateUpdated"] = dict_date_to_epoch(application, 'DateUpdated')

        application["Versions"] = json.dumps(application["Versions"])
        application["ConfigurationTemplates"] = json.dumps(application["ConfigurationTemplates"])
        application["ResourceLifecycleConfig"] = json.dumps(application["ResourceLifecycleConfig"])

        neo4j_session.run(
            ingest_distribution,
            distribution=application,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        load_elasticbeanstalk_versions(
            neo4j_session,
            application["ApplicationArn"],
            application['VersionsList'],
            current_aws_account_id,
            aws_update_tag, )

        load_elasticbeanstalk_enviroments(
            neo4j_session,
            application["ApplicationArn"],
            application['EnvironmentsList'],
            current_aws_account_id,
            aws_update_tag, )


@timeit
def sync_elastic_bean_stalk(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        current_aws_account_id: str,
        aws_update_tag: int,
) -> None:
    applications_data = get_elasticbeanstalk_applications(boto3_session)
    load_elasticbeanstalk_applications(
        neo4j_session, applications_data, current_aws_account_id,
        aws_update_tag,
    )


@timeit
def cleanup_elasticbeanstalk(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_elasticbeanstalk_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict,
) -> None:
    logger.info(f"Syncing Elastic Bean Stalk in account '{current_aws_account_id}'.")
    sync_elastic_bean_stalk(neo4j_session, boto3_session, current_aws_account_id, update_tag)
    cleanup_elasticbeanstalk(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type='AWSAccount',
        group_id=current_aws_account_id,
        synced_type='CloudFrontDistribution',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

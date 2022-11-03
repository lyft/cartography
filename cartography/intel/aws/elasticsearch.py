import time
import json
import logging
from typing import Dict
from typing import List

import boto3
import botocore.config
import neo4j
from policyuniverse.policy import Policy
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.dns import ingest_dns_record_by_fqdn
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()

# TODO get this programmatically
# https://docs.aws.amazon.com/general/latest/gr/rande.html#elasticsearch-service-regions
es_regions = [
    'us-east-2',
    'us-east-1',
    'us-west-1',
    'us-west-2',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-south-1',
    'ap-southeast-1',
    'ca-central-1',
    # 'cn-northwest-1',  -- intentionally ignored. need specific token
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'eu-west-3',
    'sa-east-1',
    # 'us-gov-west-1', -- intentionally ignored, need specific token
]


# TODO memoize this
def _get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        retries={
            'max_attempts': 8,
        },
    )


@timeit
@aws_handle_regions
def _get_es_domains(client: botocore.client.BaseClient) -> List[Dict]:
    """
    Get ES domains.

    :param client: ES boto client
    :return: list of ES domains
    """
    data = client.list_domain_names()
    domain_names = [d['DomainName'] for d in data.get('DomainNames', [])]
    # NOTE describe_elasticsearch_domains takes at most 5 domain names
    domain_name_chunks = [domain_names[i:i + 5] for i in range(0, len(domain_names), 5)]
    domains: List[Dict] = []
    for domain_name_chunk in domain_name_chunks:
        chunk_data = client.describe_elasticsearch_domains(DomainNames=domain_name_chunk)
        domains.extend(chunk_data['DomainStatusList'])
    return domains

@timeit
def transfrom_es_domains(dms: List[Dict], region: str, account_id: str) -> List[Dict]:
    domains= []
    for domain in dms:
        domain['arn'] = f"arn:aws:es:{region if region else ''}:{account_id if account_id else ''}:domain/{domain['DomainName']}"
        domain['consolelink'] = aws_console_link.get_console_link(arn=domain['arn'])
        domain['region'] = region
        domain['isPublicFacing'] = False
        if not domain.get('VPCOptions', {}).get('VpcId'):
            domain['isPublicFacing'] = True
        domains.append(domain)

    return domains

@timeit
def _load_es_domains(
    neo4j_session: neo4j.Session, domain_list: List[Dict], aws_account_id: str, aws_update_tag: int,
) -> None:
    """
    Ingest Elastic Search domains

    :param neo4j_session: Neo4j session object
    :param aws_account_id: The AWS account related to the domains
    :param domains: Domain list to ingest
    """
    ingest_records = """
    UNWIND {Records} as record
    MERGE (es:ESDomain{id: record.DomainId})
    ON CREATE SET es.firstseen = timestamp(), es.arn = record.ARN, es.domainid = record.DomainId
    SET es.lastupdated = {aws_update_tag}, es.deleted = record.Deleted, es.created = record.created,
    es.endpoint = record.Endpoint, es.elasticsearch_version = record.ElasticsearchVersion,
    es.elasticsearch_cluster_config_instancetype = record.ElasticsearchClusterConfig.InstanceType,
    es.elasticsearch_cluster_config_instancecount = record.ElasticsearchClusterConfig.InstanceCount,
    es.elasticsearch_cluster_config_dedicatedmasterenabled = record.ElasticsearchClusterConfig.DedicatedMasterEnabled,
    es.elasticsearch_cluster_config_zoneawarenessenabled = record.ElasticsearchClusterConfig.ZoneAwarenessEnabled,
    es.elasticsearch_cluster_config_dedicatedmastertype = record.ElasticsearchClusterConfig.DedicatedMasterType,
    es.elasticsearch_cluster_config_dedicatedmastercount = record.ElasticsearchClusterConfig.DedicatedMasterCount,
    es.ebs_options_ebsenabled = record.EBSOptions.EBSEnabled,
    es.ebs_options_volumetype = record.EBSOptions.VolumeType,
    es.ebs_options_volumesize = record.EBSOptions.VolumeSize,
    es.region = record.region,
    es.consolelink = record.consolelink,
    es.isPublicFacing = record.isPublicFacing,
    es.ebs_options_iops = record.EBSOptions.Iops,
    es.encryption_at_rest_options_enabled = record.EncryptionAtRestOptions.Enabled,
    es.encryption_at_rest_options_kms_key_id = record.EncryptionAtRestOptions.KmsKeyId,
    es.log_publishing_options_cloudwatch_log_group_arn = record.LogPublishingOptions.CloudWatchLogsLogGroupArn,
    es.log_publishing_options_enabled = record.LogPublishingOptions.Enabled
    WITH es
    MATCH (account:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (account)-[r:RESOURCE]->(es)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    # TODO this is a hacky workaround -- neo4j doesn't accept datetime objects and this section of the object
    # TODO contains one. we really shouldn't be sending the entire object to neo4j
    for d in domain_list:
        del d['ServiceSoftwareOptions']

    neo4j_session.run(
        ingest_records,
        Records=domain_list,
        AWS_ACCOUNT_ID=aws_account_id,
        aws_update_tag=aws_update_tag,
    )

    for domain in domain_list:
        domain_id = domain["DomainId"]
        _link_es_domains_to_dns(neo4j_session, domain_id, domain, aws_update_tag)
        _link_es_domain_vpc(neo4j_session, domain_id, domain, aws_update_tag)
        _process_access_policy(neo4j_session, domain_id, domain)


@timeit
def _link_es_domains_to_dns(
    neo4j_session: neo4j.Session, domain_id: str, domain_data: Dict, aws_update_tag: int,
) -> None:
    """
    Link the ES domain to its DNS FQDN endpoint and create associated nodes in the graph
    if needed

    :param neo4j_session: Neo4j session object
    :param domain_id: ES domain id
    :param domain_data: domain data
    """
    # TODO add support for endpoints to this method
    if domain_data.get("Endpoint"):
        ingest_dns_record_by_fqdn(
            neo4j_session, aws_update_tag, domain_data["Endpoint"], domain_id,
            record_label="ESDomain", dns_node_additional_label="AWSDNSRecord",
        )
    else:
        logger.debug(f"No es endpoint data for domain id {domain_id}")


@timeit
def _link_es_domain_vpc(neo4j_session: neo4j.Session, domain_id: str, domain_data: Dict, aws_update_tag: int) -> None:
    """
    Link the ES domain to its DNS FQDN endpoint and create associated nodes in the graph
    if needed

    :param neo4j_session: Neo4j session object
    :param domain_id: ES domain id
    :param domain_data: domain data
    """
    ingest_subnet = """
    MATCH (es:ESDomain{id: {DomainId}})
    WITH es
    UNWIND {SubnetList} as subnet_id
        MATCH (subnet_node:EC2Subnet{id: subnet_id})
        MERGE (es)-[r:PART_OF_SUBNET]->(subnet_node)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """

    ingest_sec_groups = """
    MATCH (es:ESDomain{id: {DomainId}})
    WITH es
    UNWIND {SecGroupList} as ecsecgroup_id
        MATCH (group_node:EC2SecurityGroup{id: ecsecgroup_id})
        MERGE (es)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group_node)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}
    """
    # TODO we really shouldn't be sending full objects to Neo4j
    if domain_data.get("VPCOptions"):
        vpc_data = domain_data["VPCOptions"]
        subnetList = vpc_data.get("SubnetIds", [])
        groupList = vpc_data.get("SecurityGroupIds", [])

        if len(subnetList) > 0:
            neo4j_session.run(
                ingest_subnet,
                DomainId=domain_id,
                SubnetList=subnetList,
                aws_update_tag=aws_update_tag,
            )

        if len(groupList) > 0:
            neo4j_session.run(
                ingest_sec_groups,
                DomainId=domain_id,
                SecGroupList=groupList,
                aws_update_tag=aws_update_tag,
            )


@timeit
def _process_access_policy(neo4j_session: neo4j.Session, domain_id: str, domain_data: Dict) -> None:
    """
    Link the ES domain to its DNS FQDN endpoint and create associated nodes in the graph
    if needed

    :param neo4j_session: Neo4j session object
    :param domain_id: ES domain id
    :param domain_data: domain data
    """
    tag_es = "MATCH (es:ESDomain{id: {DomainId}}) SET es.exposed_internet = {InternetExposed}"

    exposed_internet = False

    if domain_data.get("Endpoint") and domain_data.get("AccessPolicies"):
        policy = Policy(json.loads(domain_data['AccessPolicies']))
        if policy.is_internet_accessible():
            exposed_internet = True

    neo4j_session.run(tag_es, DomainId=domain_id, InternetExposed=exposed_internet)


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_es_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
@aws_handle_regions
def get_elasticsearch_reserved_instances(client: botocore.client.BaseClient, region: str, current_aws_account_id: str) -> List[Dict]:
    reserved_instances = []
    try:
        paginator = client.get_paginator('describe_reserved_elasticsearch_instances')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            reserved_instances.extend(page.get('ReservedElasticsearchInstances', []))
        for reserved_instance in reserved_instances:
            reserved_instance['arn'] = f"arn:aws:es:{region}:{current_aws_account_id}:reserved-instances/{reserved_instance['ReservedElasticsearchInstanceId']}"
            reserved_instance['region'] = region

        return reserved_instances

    except ClientError as e:
        logger.error(f'Failed to call ES describe_reserved_elasticsearch_instances: {region} - {e}')
        return reserved_instances


def load_elasticsearch_reserved_instances(session: neo4j.Session, reserved_instances: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.write_transaction(_load_elasticsearch_reserved_instances_tx,
                              reserved_instances, current_aws_account_id, aws_update_tag)


@timeit
def _load_elasticsearch_reserved_instances_tx(tx: neo4j.Transaction, reserved_instances: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND {Records} as record
    MERGE (instance:AWSESReservedInstance{id: record.arn})
    ON CREATE SET instance.firstseen = timestamp(),
        instance.arn = record.arn
    SET instance.lastupdated = {aws_update_tag},
        instance.name = record.ReservedElasticsearchInstanceId,
        instance.region = record.region,
        instance.fixed_price = record.FixedPrice,
        instance.reserved_elasticsearch_instance_offering_id = record.ReservedElasticsearchInstanceOfferingId,
        instance.reservation_name = record.ReservationName,
        instance.payment_option = record.PaymentOption,
        instance.usage_price = record.UsagePrice,
        instance.state = record.State,
        instance.start_time = record.StartTime,
        instance.elasticsearch_instance_count = record.ElasticsearchInstanceCount,
        instance.duration = record.Duration,
        instance.elasticsearch_instance_type = record.ElasticsearchInstanceType,
        instance.currency_code = record.CurrencyCode
    WITH instance
    MATCH (owner:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (owner)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    tx.run(
        query,
        Records=reserved_instances,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_elasticsearch_reserved_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_elasticsearch_reserved_instance_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Elasticsearch Service for account '%s', at %s.", current_aws_account_id, tic)

    data = []
    reserved_instances = []
    for region in es_regions:
        client = boto3_session.client('es', region_name=region, config=_get_botocore_config())
        domains = _get_es_domains(client)
        data = transfrom_es_domains(domains, region, current_aws_account_id)
        reserved_instances.extend(get_elasticsearch_reserved_instances(client, region, current_aws_account_id))

    logger.info(f"Total ElasticSearch Domains: {len(data)}")

    logger.info(f"Total ElasticSearch Reserved Instances: {len(data)}")

    if common_job_parameters.get('pagination', {}).get('elasticsearch', None):
        pageNo = common_job_parameters.get("pagination", {}).get("elasticsearch", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("elasticsearch", None)["pageSize"]
        totalPages = len(data) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(f'pages process for elasticsearch domains {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('elasticsearch', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('elasticsearch', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('elasticsearch', {})['pageSize']
        if page_end > len(data) or page_end == len(data):
            data = data[page_start:]
        else:
            has_next_page = True
            data = data[page_start:page_end]
            common_job_parameters['pagination']['elasticsearch']['hasNextPage'] = has_next_page

    _load_es_domains(neo4j_session, data, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    if common_job_parameters.get('pagination', {}).get('elasticsearch', None):
        pageNo = common_job_parameters.get("pagination", {}).get("elasticsearch", None)["pageNo"]
        pageSize = common_job_parameters.get("pagination", {}).get("elasticsearch", None)["pageSize"]
        totalPages = len(reserved_instances) / pageSize
        if int(totalPages) != totalPages:
            totalPages = totalPages + 1
        totalPages = int(totalPages)
        if pageNo < totalPages or pageNo == totalPages:
            logger.info(
                f'pages process for elasticsearch reserved instances {pageNo}/{totalPages} pageSize is {pageSize}')
        page_start = (common_job_parameters.get('pagination', {}).get('elasticsearch', {})[
                      'pageNo'] - 1) * common_job_parameters.get('pagination', {}).get('elasticsearch', {})['pageSize']
        page_end = page_start + common_job_parameters.get('pagination', {}).get('elasticsearch', {})['pageSize']
        if page_end > len(reserved_instances) or page_end == len(reserved_instances):
            reserved_instances = reserved_instances[page_start:]
        else:
            has_next_page = True
            reserved_instances = reserved_instances[page_start:page_end]
            common_job_parameters['pagination']['elasticsearch']['hasNextPage'] = has_next_page

    load_elasticsearch_reserved_instances(neo4j_session, reserved_instances, current_aws_account_id, update_tag)
    cleanup_elasticsearch_reserved_instances(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Elasticsearch Service: {toc - tic:0.4f} seconds")

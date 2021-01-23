import logging
from string import Template

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_network_acl_data(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_network_acls')
    network_acls = []
    for page in paginator.paginate():
        network_acls.extend(page['NetworkAcls'])
    return network_acls


@timeit
def _get_rules_statement():
    INGEST_RULE_TEMPLATE = """
    UNWIND {NetworkAcls} as network_acl
    MATCH (nacl:NetworkAcl{id: network_acl.NetworkAclId})
    WITH nacl, network_acl
    UNWIND network_acl.Entries as entry
        MERGE (new_rule:NetworkAclRule{id: network_acl.NetworkAclId + '|' + 
        Case entry.Egress when true then 'egress' else 'ingress' end + 
        '|' + entry.RuleNumber})
        ON CREATE SET new_rule.firstseen = timestamp()
        SET new_rule.cidr_block = entry.CidrBlock,
        new_rule.ipv6_cidr_block = entry.Ipv6CidrBlock,
        new_rule.egress = entry.Egress,
        new_rule.protocol = entry.Protocol,
        new_rule.rule_action = entry.RuleAction,
        new_rule.rule_number = entry.RuleNumber,
        new_rule.icmp_code = entry.IcmpTypeCode.code,
        new_rule.icmp_type = entry.IcmpTypecode.type,
        new_rule.port_range_from = entry.PortRange.From,
        new_rule.port_range_to = entry.PortRange.To,
        new_rule.lastupdated = {aws_update_tag}
        WITH nacl, new_rule
        MERGE (new_rule)-[r:RULE_OF_NETWORK_ACL]->(nacl)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {aws_update_tag}"""

    return INGEST_RULE_TEMPLATE


@timeit
def load_entries(neo4j_session, network_acls, aws_update_tag):
    ingest_statement = _get_rules_statement()
    neo4j_session.run(
        ingest_statement,
        NetworkAcls=network_acls,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_subnet_associations(neo4j_session, network_acls, aws_update_tag):
    ingest_network_acl_subnet_relations = """
    UNWIND {NetworkAcls} as network_acl
    WITH network_acl
    UNWIND network_acl.Associations as association
    MATCH (nacl:NetworkAcl{id: network_acl.NetworkAclId}), (snet:EC2Subnet{subnetid: association.SubnetId})
    MERGE (nacl)<-[r:SUBNET_ASSOCIATION]-(snet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag},
    r.network_acl_association_id = association.NetworkAclAssociationId
    """
    neo4j_session.run(
        ingest_network_acl_subnet_relations,
        NetworkAcls=network_acls,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_network_acls(neo4j_session, data, region, aws_account_id, aws_update_tag):

    ingest_network_acls = """
    UNWIND {network_acls} as network_acl
    MERGE (nacl:NetworkAcl{id: network_acl.NetworkAclId})
    ON CREATE SET nacl.firstseen = timestamp()
    SET nacl.lastupdated = {aws_update_tag},
    nacl.is_default = network_acl.IsDefault,
    nacl.region = {region},
    nacl.vpc_id = network_acl.VpcId,
    nacl.network_acl_id = network_acl.NetworkAclId
    """

    ingest_network_acl_vpc_relations = """
    UNWIND {network_acls} as network_acl
    MATCH (nacl:NetworkAcl{id: network_acl.NetworkAclId}), (vpc:AWSVpc{id: network_acl.VpcId})
    MERGE (nacl)-[r:MEMBER_OF_AWS_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_network_acl_aws_account_relations = """
    UNWIND {network_acls} as network_acl
    MATCH (nacl:NetworkAcl{id: network_acl.NetworkAclId}), (aws:AWSAccount{id: {aws_account_id}})
    MERGE (aws)-[r:RESOURCE]->(nacl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    neo4j_session.run(
        ingest_network_acls, network_acls=data, aws_update_tag=aws_update_tag, region=region
    )

    neo4j_session.run(
        ingest_network_acl_vpc_relations, network_acls=data, aws_update_tag=aws_update_tag
    )

    neo4j_session.run(
        ingest_network_acl_aws_account_relations, network_acls=data, aws_update_tag=aws_update_tag,
        aws_account_id=aws_account_id,
    )

    load_entries(
        neo4j_session,
        network_acls=data,
        aws_update_tag=aws_update_tag,
    )
    load_subnet_associations(
        neo4j_session,
        network_acls=data,
        aws_update_tag=aws_update_tag
    )


@timeit
def cleanup_network_acls(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_network_acl_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_network_acls(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.info("Syncing EC2 network_acls for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_network_acl_data(boto3_session, region)
        load_network_acls(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_network_acls(neo4j_session, common_job_parameters)

import logging
from string import Template

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_security_group_data(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_security_groups')
    security_groups = []
    for page in paginator.paginate():
        security_groups.extend(page['SecurityGroups'])
    return security_groups


@timeit
def load_ec2_security_group_rule(neo4j_session, group, rule_type, aws_update_tag):
    INGEST_RULE_TEMPLATE = Template("""
    MERGE (rule:$rule_label{ruleid: {RuleId}})
    ON CREATE SET rule :IpRule, rule.firstseen = timestamp(), rule.fromport = {FromPort}, rule.toport = {ToPort},
    rule.protocol = {Protocol}
    SET rule.lastupdated = {aws_update_tag}
    WITH rule
    MATCH (group:EC2SecurityGroup{groupid: {GroupId}})
    MERGE (group)<-[r:MEMBER_OF_EC2_SECURITY_GROUP]-(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag};
    """)

    ingest_rule_group_pair = """
    MERGE (group:EC2SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.lastupdated = {aws_update_tag}
    WITH group
    MATCH (inbound:IpRule{ruleid: {RuleId}})
    MERGE (inbound)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    ingest_range = """
    MERGE (range:IpRange{id: {RangeId}})
    ON CREATE SET range.firstseen = timestamp(), range.range = {RangeId}
    SET range.lastupdated = {aws_update_tag}
    WITH range
    MATCH (rule:IpRule{ruleid: {RuleId}})
    MERGE (rule)<-[r:MEMBER_OF_IP_RULE]-(range)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """

    group_id = group["GroupId"]
    rule_type_map = {"IpPermissions": "IpPermissionInbound", "IpPermissionEgress": "IpPermissionEgress"}

    if group.get(rule_type):
        for rule in group[rule_type]:
            protocol = rule.get("IpProtocol", "all")
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")

            ruleid = f"{group_id}/{rule_type}/{from_port}{to_port}{protocol}"
            # NOTE Cypher query syntax is incompatible with Python string formatting, so we have to do this awkward
            # NOTE manual formatting instead.
            neo4j_session.run(
                INGEST_RULE_TEMPLATE.safe_substitute(rule_label=rule_type_map[rule_type]),
                RuleId=ruleid,
                FromPort=from_port,
                ToPort=to_port,
                Protocol=protocol,
                GroupId=group_id,
                aws_update_tag=aws_update_tag,
            )

            neo4j_session.run(
                ingest_rule_group_pair,
                GroupId=group_id,
                RuleId=ruleid,
                aws_update_tag=aws_update_tag,
            )

            for ip_range in rule["IpRanges"]:
                range_id = ip_range["CidrIp"]
                neo4j_session.run(
                    ingest_range,
                    RangeId=range_id,
                    RuleId=ruleid,
                    aws_update_tag=aws_update_tag,
                )


@timeit
def load_ec2_security_groupinfo(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_security_group = """
    MERGE (group:EC2SecurityGroup{id: {GroupId}})
    ON CREATE SET group.firstseen = timestamp(), group.groupid = {GroupId}
    SET group.name = {GroupName}, group.description = {Description}, group.region = {Region},
    group.lastupdated = {aws_update_tag}
    WITH group
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    WITH group
    MATCH (vpc:AWSVpc{id: {VpcId}})
    MERGE (vpc)-[rg:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET rg.firstseen = timestamp()
    """

    for group in data:
        group_id = group["GroupId"]

        neo4j_session.run(
            ingest_security_group,
            GroupId=group_id,
            GroupName=group.get("GroupName"),
            Description=group.get("Description"),
            VpcId=group.get("VpcId", None),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        load_ec2_security_group_rule(neo4j_session, group, "IpPermissions", aws_update_tag)
        load_ec2_security_group_rule(neo4j_session, group, "IpPermissionEgress", aws_update_tag)


@timeit
def cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters):
    run_cleanup_job(
        'aws_import_ec2_security_groupinfo_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_security_groupinfo(
        neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
        common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 security groups for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_security_group_data(boto3_session, region)
        load_ec2_security_groupinfo(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_security_groupinfo(neo4j_session, common_job_parameters)

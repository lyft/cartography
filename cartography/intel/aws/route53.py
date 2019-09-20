import logging

from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def link_aws_resources(neo4j_session, update_tag):
    # find records that point to other records
    link_records = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (v:AWSDNSRecord{value: n.name})
    MERGE (v)-[p:DNS_POINTS_TO]->(n)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(link_records, aws_update_tag=update_tag)

    # find records that point to AWS LoadBalancers
    link_elb = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (l:LoadBalancer{dnsname: n.value})
    MERGE (n)-[p:DNS_POINTS_TO]->(l)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(link_elb, aws_update_tag=update_tag)

    # find records that point to AWS EC2 Instances
    link_ec2 = """
    MATCH (n:AWSDNSRecord) WITH n MATCH (e:EC2Instance{publicdnsname: n.value})
    MERGE (n)-[p:DNS_POINTS_TO]->(e)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(link_ec2, aws_update_tag=update_tag)


def load_a_records(neo4j_session, records, update_tag):
    ingest_records = """
    UNWIND {records} as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name, a.type = record.type
    SET a.lastupdated = {aws_update_tag}, a.value = record.value
    WITH a,record
    MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
    MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        aws_update_tag=update_tag,
    )


def load_alias_records(neo4j_session, records, update_tag):
    # create the DNSRecord nodes and link them to matching DNSZone and S3Bucket nodes
    ingest_records = """
    UNWIND {records} as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name, a.type = record.type
    SET a.lastupdated = {aws_update_tag}, a.value = record.value
    WITH a,record
    MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
    MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        aws_update_tag=update_tag,
    )


def load_cname_records(neo4j_session, records, update_tag):
    ingest_records = """
    UNWIND {records} as record
    MERGE (a:DNSRecord:AWSDNSRecord{id: record.id})
    ON CREATE SET a.firstseen = timestamp(), a.name = record.name, a.type = record.type
    SET a.lastupdated = {aws_update_tag}, a.value = record.value
    WITH a,record
    MATCH (zone:AWSDNSZone{zoneid: record.zoneid})
    MERGE (a)-[r:MEMBER_OF_DNS_ZONE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_records,
        records=records,
        aws_update_tag=update_tag,
    )


def load_zone(neo4j_session, zone, current_aws_id, update_tag):
    ingest_z = """
    MERGE (zone:DNSZone:AWSDNSZone{name: {ZoneName}})
    ON CREATE SET zone.firstseen = timestamp(), zone.zoneid = {ZoneId}
    SET zone.lastupdated = {aws_update_tag}, zone.comment = {Comment}, zone.privatezone = {PrivateZone}
    WITH zone
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(zone)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
    """
    neo4j_session.run(
        ingest_z,
        ZoneName=zone['name'][:-1],
        ZoneId=zone['zoneid'],
        Comment=zone['comment'],
        PrivateZone=zone['privatezone'],
        AWS_ACCOUNT_ID=current_aws_id,
        aws_update_tag=update_tag,
    )


def parse_record_set(record_set, zone_id):
    # process CNAME, ALIAS and A records
    if record_set['Type'] == 'CNAME':
        if 'AliasTarget' in record_set:
            # this is a weighted CNAME record
            value = record_set['AliasTarget']['DNSName']
            if value.endswith('.'):
                value = value[:-1]
            return {
                "name": record_set['Name'][:-1],
                "type": 'CNAME',
                "zoneid": zone_id,
                "value": value,
                "id": record_set['Name'][:-1] + '+WEIGHTED_CNAME',
            }
        else:
            # This is a normal CNAME record
            value = record_set['ResourceRecords'][0]['Value']
            if value.endswith('.'):
                value = value[:-1]
            return {
                "name": record_set['Name'][:-1],
                "type": 'CNAME',
                "zoneid": zone_id,
                "value": value,
                "id": record_set['Name'][:-1] + '+CNAME',
            }

    elif record_set['Type'] == 'A':
        if 'AliasTarget' in record_set:
            # this is an ALIAS record
            # ALIAS records are a special AWS-only type of A record
            return {
                "name": record_set['Name'][:-1],
                "type": 'ALIAS',
                "zoneid": zone_id,
                "value": record_set['AliasTarget']['DNSName'][:-1],
                "id": record_set['Name'][:-1] + '+ALIAS',
            }
        else:
            # this is a real A record
            # loop and add each value (IP address) to a comma separated string
            # don't forget to trim that trailing comma!
            # TODO can this be replaced with a string join?
            value = ''
            for a_value in record_set['ResourceRecords']:
                value = value + a_value['Value'] + ','

            return {
                "name": record_set['Name'][:-1],
                "type": 'A',
                "zoneid": zone_id,
                "value": value[:-1],
                "id": record_set['Name'][:-1] + '+A',
            }


def parse_zone(zone):
    # TODO simplify this
    if 'Comment' in zone['Config']:
        comment = zone['Config']['Comment']
    else:
        comment = ''

    return {
        "zoneid": zone['Id'],
        "name": zone['Name'],
        "privatezone": zone['Config']['PrivateZone'],
        "comment": comment,
        "count": zone['ResourceRecordSetCount'],
    }


def load_dns_details(neo4j_session, dns_details, current_aws_id, update_tag):
    for zone, zone_record_sets in dns_details:
        zone_a_records = []
        zone_alias_records = []
        zone_cname_records = []

        parsed_zone = parse_zone(zone)

        load_zone(neo4j_session, parsed_zone, current_aws_id, update_tag)

        for record_set in zone_record_sets:
            if record_set['Type'] == 'A' or record_set['Type'] == 'CNAME':
                record = parse_record_set(record_set, zone['Id'])

                if record['type'] == 'A':
                    zone_a_records.append(record)
                elif record['type'] == 'ALIAS':
                    zone_alias_records.append(record)
                elif record['type'] == 'CNAME':
                    zone_cname_records.append(record)

        if zone_a_records:
            load_a_records(neo4j_session, zone_a_records, update_tag)

        if zone_alias_records:
            load_alias_records(neo4j_session, zone_alias_records, update_tag)

        if zone_cname_records:
            load_cname_records(neo4j_session, zone_cname_records, update_tag)

    link_aws_resources(neo4j_session, update_tag)


def get_zone_record_sets(client, zone_id):
    resource_record_sets = []
    paginator = client.get_paginator('list_resource_record_sets')
    pages = paginator.paginate(HostedZoneId=zone_id)
    for page in pages:
        resource_record_sets.extend(page['ResourceRecordSets'])
    return resource_record_sets


def get_zones(client):
    paginator = client.get_paginator('list_hosted_zones')
    hosted_zones = []
    for page in paginator.paginate():
        hosted_zones.extend(page['HostedZones'])

    results = []
    for hosted_zone in hosted_zones:
        record_sets = get_zone_record_sets(client, hosted_zone['Id'])
        results.append((hosted_zone, record_sets))
    return results


def cleanup_route53(neo4j_session, current_aws_id, update_tag):
    run_cleanup_job(
        'aws_dns_cleanup.json',
        neo4j_session,
        {'UPDATE_TAG': update_tag, 'AWS_ID': current_aws_id},
    )


def sync(neo4j_session, boto3_session, aws_id, update_tag):
    logger.info("Syncing Route53 for account '%s'.", aws_id)
    client = boto3_session.client('route53')
    zones = get_zones(client)
    load_dns_details(neo4j_session, zones, aws_id, update_tag)
    cleanup_route53(neo4j_session, aws_id, update_tag)

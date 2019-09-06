import logging

import dns.rdatatype
import dns.resolver

logger = logging.getLogger(__name__)


def ingest_dns_record_by_fqdn(neo4j_session, update_tag, fqdn, points_to_record):
    """
    Ingest a new DNS record by it's FQDN

    :param neo4j_session: Neo4j session object
    :param update_tag: Update tag to set the node with and childs
    :param fqdn: the fqdn record to add
    :param points_to_record: parent record to set DNS_POINTS_TO relationship to. Can be None
    :return: the graph node id for the new/merged record
    """
    fqdn_data = get_dns_resolution_by_fqdn(fqdn)
    record_type = get_dns_record_type(fqdn_data)

    if record_type == 'A':
        ip_list = []
        for result in fqdn_data:
            ip = str(result)
            ip_list.append(ip)

        value = ",".join(ip_list)
        record_id = ingest_dns_record(neo4j_session, fqdn, value, record_type, update_tag, points_to_record)
        _link_ip_to_A_record(neo4j_session, update_tag, ip_list, record_id)

        return record_id
    else:
        raise NotImplementedError(
            "Ingestion of DNS record type '{}' by FQDN has not been implemented. Failed to ingest '{}'.".format(
                record_type,
                fqdn,
            ),
        )


def _link_ip_to_A_record(neo4j_session, update_tag, ip_list, parent_record):
    """
    Link A record to to its IP

    :param neo4j_session: Neo4j session object
    :param update_tag: Update tag to set the node with and childs
    :param ip_list: List of IP to link
    :param parent_record: parent record to set DNS_POINTS_TO relationship to
    """
    ingest = """
    MATCH (parent:DNSRecord{id: {ParentId}})
    WITH parent
    UNWIND {IP_LIST} as current_ip
    MERGE (ip_node:Ip{id: current_ip})
    ON CREATE SET ip_node.firstseen = timestamp(), ip_node.ip = current_ip
    SET ip_node.lastupdated = {update_tag}
    WITH parent, ip_node
    MERGE (parent)-[r:DNS_POINTS_TO]->(ip_node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    neo4j_session.run(
        ingest,
        ParentId=parent_record,
        IP_LIST=ip_list,
        update_tag=update_tag,
    )


def ingest_dns_record(neo4j_session, name, value, type, update_tag, points_to_record):
    """
    Ingest a new DNS record

    :param neo4j_session: Neo4j session object
    :param name: record name
    :param value: record value
    :param type: record type
    :param update_tag: Update tag to set the node with and childs
    :param points_to_record: parent record to set DNS_POINTS_TO relationship to. Can be None
    :return: the intel graph node id for the new/merged record
    """
    ingest = """
    MERGE (record:DNSRecord{id: {Id}})
    ON CREATE SET record.firstseen = timestamp(), record.name = {Name}, record.type = {Type}
    SET record.lastupdated = {update_tag}, record.value = {Value}
    WITH record
    MATCH (n{id: {PointsToId}})
    MERGE (record)-[r:DNS_POINTS_TO]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {update_tag}
    """

    record_id = f"{name}+{type}"

    neo4j_session.run(
        ingest,
        Id=record_id,
        Name=name,
        Type=type,
        Value=value,
        PointsToId=points_to_record,
        update_tag=update_tag,
    )

    return record_id


def get_dns_resolution_by_fqdn(fqdn):
    """
    Get dns resolution data for fqdn

    :param fqdn: record to query
    :return: DNS resolution Answer as dns.resolver.Answer
    """
    return dns.resolver.query(fqdn)


def get_dns_record_type(record_data):
    """
    Get DNS record type from answer

    :param record_data: dns resolution data
    :return: record type (A,CNAME, ...)
    """
    return dns.rdatatype.to_text(record_data.rdtype)

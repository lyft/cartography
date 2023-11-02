import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
from cloudconsolelink.clouds.aws import AWSLinker
import time
logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()



@timeit
@aws_handle_regions
def get_elastic_ip_addresses(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    addresses = []
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    try:
        addresses = client.describe_addresses()['Addresses']
        for address in addresses:
            address['region'] = region

    except Exception as e:
        logger.warning(f"Failed retrieve address for region - {region}. Error - {e}")

    return addresses


@timeit
def transform_elastic_ip_addresses(elastic_ip_addresses: List[Dict], current_aws_account_id: str,) -> List[Dict]:
    addresses: List[Dict] = []
    for address in elastic_ip_addresses:
        address['arn'] = f"arn:aws:ec2:{address.get('region')}:{current_aws_account_id}:elastic-ip/{address.get('AllocationId')}"
        address['consolelink'] = aws_console_link.get_console_link(arn=address['arn'])
        if address.get('AllocationId'):
            addresses.append(address)

    return addresses

@timeit
def load_elastic_ip_addresses(
    neo4j_session: neo4j.Session, elastic_ip_addresses: List[Dict],
    current_aws_account_id: str, update_tag: int,
) -> None:
    """
    Creates (:ElasticIPAddress)
    (:ElasticIPAddress)-[:RESOURCE]->(:AWSAccount),
    (:EC2Instance)-[:ELASTIC_IP_ADDRESS]->(:ElasticIPAddress),
    (:NetworkInterface)-[:ELASTIC_IP_ADDRESS]->(:ElasticIPAddress),
    """
    logger.info(f"Loading {len(elastic_ip_addresses)} Elastic IP Addresses")
    ingest_addresses = """
    UNWIND $elastic_ip_addresses as eia
        MERGE (address: ElasticIPAddress{id: eia.AllocationId})
        ON CREATE SET address.firstseen = timestamp()
        SET address.instance_id = eia.InstanceId, address.public_ip = eia.PublicIp,
        address.name = eia.AllocationId,
        address.allocation_id = eia.AllocationId, address.association_id = eia.AssociationId,
        address.domain = eia.Domain, address.network_interface_id = eia.NetworkInterfaceId,
        address.network_interface_owner_id = eia.NetworkInterfaceOwnerId,
        address.consolelink = eia.consolelink,
        address.private_ip_address = eia.PrivateIpAddress, address.public_ipv4_pool = eia.PublicIpv4Pool,
        address.network_border_group = eia.NetworkBorderGroup, address.customer_owned_ip = eia.CustomerOwnedIp,
        address.customer_owned_ipv4_pool = eia.CustomerOwnedIpv4Pool, address.carrier_ip = eia.CarrierIp,
        address.region = address.region, address.lastupdated = $update_tag, address.arn = eia.arn
        WITH address

        MATCH (account:AWSAccount{id: $aws_account_id})
        MERGE (account)-[r:RESOURCE]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH address

        MATCH (instance:EC2Instance) WHERE instance.id = address.instance_id
        MERGE (instance)-[r:ELASTIC_IP_ADDRESS]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH address

        MATCH (ni:NetworkInterface{id: address.network_interface_id})
        MERGE (ni)-[r:ELASTIC_IP_ADDRESS]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_addresses,
        elastic_ip_addresses=elastic_ip_addresses,
        aws_account_id=current_aws_account_id,
        update_tag=update_tag,
    )


@timeit
def cleanup_elastic_ip_addresses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_elastic_ip_addresses_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_elastic_ip_addresses(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing Elastic IP Addresses for account '%s', at %s.", current_aws_account_id, tic)
    addresses = []
    for region in regions:
        logger.info(f"Syncing Elastic IP Addresses for region {region} in account {current_aws_account_id}.")
        addresses.extend(get_elastic_ip_addresses(boto3_session, region))

    logger.info(f"Total Elastic IP Addresses: {len(addresses)}")

    addresses = transform_elastic_ip_addresses(addresses, current_aws_account_id)
    load_elastic_ip_addresses(neo4j_session, addresses, current_aws_account_id, update_tag)
    cleanup_elastic_ip_addresses(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Elastic IP Addresses: {toc - tic:0.4f} seconds")

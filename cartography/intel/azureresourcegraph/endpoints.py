"""
cartography/intel/azureresourcegraph/endpoints
"""
# pylint: disable=missing-function-docstring,too-many-arguments
import logging
from typing import Dict
from typing import List

import neo4j

from .util import azureresourcegraph_hosts
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: str,
) -> None:
    arg_hosts_list = azureresourcegraph_hosts(authorization)
    for host_data in arg_hosts_list:
        load_host_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information

    resourceid,instance_id,subscriptionId,subscriptionName, resourceGroup, name, type, vmStatus,
    tags.environment, tags.costcenter, tags.contact, tags.businessproduct, tags.businesscontact,
    tags.engproduct, tags.engcontact, tags.lob, tags.compliance, tags.ticket,
    subproperties,publicIpName,publicIPAllocationMethod,ipAddress,nsgId

    FIXME! create duplicate entries/not merging
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:AzureResourceGraphHost{id: host.resourceid})
        ON CREATE SET h.id = host.resourceid,
            h.firstseen = timestamp()
        SET h.instance_id = host.instance_id,
            h.resource_id = toLower(host.resourceid),
            h.subscription_id = host.subscriptionId,
            h.subscription_name = host.subscriptionName,
            h.resource_group = host.resourceGroup,
            h.hostname = host.name,
            h.type = host.type,
            h.osname = host.osname,
            h.ostype = host.ostype,
            h.tags_environment = host.tags_environment,
            h.tags_costcenter = host.tags_costcenter,
            h.tags_engproduct = host.tags_engproduct,
            h.tags_engcontact = host.tags_engcontact,
            h.tags_businesscontact = host.tags_businesscontact,
            h.vm_status = host.vmStatus,
            h.image_publisher = host.image_publisher,
            h.image_offer = host.image_offer,
            h.image_sku = host.image_sku,
            h.image_galleryid = host.image_galleryid,
            h.public_ip_name = host.publicIpName,
            h.public_ip_allocation_method = host.publicIPAllocationMethod,
            h.public_ip = host.ipAddress,
            h.nsg_id = host.nsgId,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureSubscription{id: h.subscription_id})
        MERGE (s)-[r:CONTAINS]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH h
        MATCH (s:AzureVirtualMachine{id: h.resource_id})
        MERGE (s)-[r:PRESENT_IN]->(h)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    logger.debug("Loading %s azureresourcegraph hosts.", len(data))
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )

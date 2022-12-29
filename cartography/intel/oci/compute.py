import logging
import re
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_instance_list_data(
    compute: oci.core.ComputeClient,
    current_tenancy_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    response = oci.pagination.list_call_get_all_results(compute.list_instances, compartment_id=current_tenancy_id)
    return {'Instances': utils.oci_object_to_json(response.data)}


def load_instances(
    neo4j_session: neo4j.Session,
    instances: List[Dict[str, Any]],
    current_tenancy_id: str,
    oci_update_tag: int,
) -> None:
    ingest_instance = """
    MERGE (pnode:OCIInstance{id: {ID}})
    ON CREATE SET pnode.firstseen = timestamp(), pnode.createdate = {CREATE_DATE}
    SET pnode.name = {INSTANCE_NAME}, pnode.compartmentid = {COMPARTMENT_ID},
    pnode.instancetype = {INSTANCE_TYPE}, pnode.region = {REGION},
    pnode.state = {STATE}, pnode.imageid = {IMAGE_ID},
    pnode.lastupdated = {oci_update_tag}
    WITH pnode
    MATCH (aa) WHERE (aa:OCITenancy OR aa:OCICompartment) AND aa.ocid={COMPARTMENT_ID}
    MERGE (aa)-[r:RESOURCE]->(pnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {oci_update_tag}
    """

    for instance in instances:
        neo4j_session.run(
            ingest_instance,
            ID=instance["id"],
            INSTANCE_NAME=instance["display-name"],
            COMPARTMENT_ID=instance["compartment-id"],
            INSTANCE_TYPE=instance["shape"],
            REGION=instance["region"],
            STATE=instance["lifecycle-state"],
            IMAGE_ID=instance["image-id"],
            CREATE_DATE=str(instance["time-created"]),
            OCI_TENANCY_ID=current_tenancy_id,
            oci_update_tag=oci_update_tag,
        )


# list_instances
def sync_instances(
    neo4j_session: neo4j.Session,
    compute: oci.core.ComputeClient,
    current_tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
):
    logger.info("Syncing compute instances for account '%s'.", current_tenancy_id)
    compartments = utils.get_compartments_in_tenancy(neo4j_session, current_tenancy_id)
    for compartment in compartments:
        logger.info(
            "Syncing OCI instances for compartment '%s' in account '%s'.", compartment['ocid'], current_tenancy_id,
        )
        data = get_instance_list_data(compute, compartment["ocid"])
        if(data["Instances"]):
            load_instances(neo4j_session, data["Instances"], current_tenancy_id, oci_update_tag)
            print(len(data["Instances"]))
        run_cleanup_job('oci_import_instances_cleanup.json', neo4j_session, common_job_parameters)

def sync(
    neo4j_session: neo4j.Session,
    compute: oci.core.ComputeClient,
    tenancy_id: str,
    region_name: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Syncing Compute for account '%s'.", tenancy_id)
    sync_instances(neo4j_session, compute, tenancy_id, oci_update_tag, common_job_parameters)

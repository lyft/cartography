import logging
from typing import Dict
from typing import List

import neo4j
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_labels(session: neo4j.Session, data_list: List[Dict], update_tag: int, common_job_parameters: Dict,) -> None:
    session.write_transaction(_load_labels_tx, data_list, update_tag, common_job_parameters)


@timeit
def get_labels_list(data: List[Dict]) -> List[Dict]:
    labels_data = []
    for item in data:
        labels = item.get('labels', {})
        if type(labels) is not dict:
            labels = {}
        for key, value in labels.items():
            label = {}
            label['id'] = f"{item.get('id','')}/label/{key}"
            label['name'] = key
            label['value'] = value
            label['resource_id'] = item.get('id', None)

            if label['resource_id']:
                labels_data.append(label)

    return labels_data


def _load_labels_tx(tx: neo4j.Transaction, data: List[Dict], update_tag: int, common_job_parameters: Dict,) -> None:
    ingest_label = """
    UNWIND {data} AS label
    MERGE (l:GCPLabel{id: label.id})
    ON CREATE SET l.firstseen = timestamp()
    SET l.lastupdated = {update_tag},
    l.value = label.value,
    l.name = label.name
    WITH l,label
    MATCH (r:""" + common_job_parameters.get('service_label', '') + """{id:label.resource_id})
    <-[:RESOURCE]-(:GCPProject{id: {GCP_PROJECT_ID}})<-[:OWNER]-(:CloudanixWorkspace{id: {WORKSPACE_ID}})
    MERGE (r)-[lb:LABELED]->(l)
    ON CREATE SET lb.firstseen = timestamp()
    SET lb.lastupdated = {update_tag}
    """

    tx.run(
        ingest_label,
        data=data,
        update_tag=update_tag,
        GCP_PROJECT_ID=common_job_parameters['GCP_PROJECT_ID'],
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
    )


def cleanup_labels(neo4j_session: neo4j.Session, common_job_parameters: Dict, service_name: str) -> None:
    logger.info(f"Cleaning Labels for {service_name}")
    run_cleanup_job('gcp_labels_cleanup.json', neo4j_session, common_job_parameters)


def sync_labels(
    neo4j_session: neo4j.Session, data: List[Dict], update_tag: int, common_job_parameters: Dict,
    service_name: str, service_label: str,
) -> None:
    if len(data) > 0:
        labels_list = get_labels_list(data)
        if len(labels_list) > 0:
            logger.info(f"Loading Labels for {service_name}")
            common_job_parameters['service_label'] = service_label
            load_labels(neo4j_session, labels_list, update_tag, common_job_parameters)
            cleanup_labels(neo4j_session, common_job_parameters, service_name)
            try:
                del common_job_parameters["service_label"]
            except KeyError as e:
                logger.warning(e)

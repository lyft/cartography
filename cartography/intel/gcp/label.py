import logging
from typing import Dict
from typing import List

import neo4j
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def load_labels(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_labels_tx, data_list, update_tag)


@timeit
def get_labels_list(data: List[Dict]) -> List[Dict]:
    labels_data = []
    for item in data:
        labels = item.get('labels', {})
        for key, value in labels.items():
            label = {}
            label['id'] = f"{item.get('id','')}/label/{key}"
            label['name'] = key
            label['value'] = value
            label['resource_id'] = item.get('id', None)

            if label['resource_id']:
                labels_data.extend(label)

    return labels_data


def _load_labels_tx(tx: neo4j.Transaction, data: List[Dict], update_tag: int) -> None:
    ingest_label = """
    UNWIND {data} AS label
    MERGE (l:GCPLabel{id: label.id})
    ON CREATE SET l.firstseen = timestamp()
    SET l.lastupdated = {update_tag},
    l.value = label.value,
    l.name = label.name
    WITH l,label
    MATCH (r) where r.id = label.resource_id
    MERGE (r)-[lb:LABELED]->(l)
    ON CREATE SET lb.firstseen = timestamp()
    SET lb.lastupdated = {update_tag}
    """

    tx.run(
        ingest_label,
        data=data,
        update_tag=update_tag,
    )


def cleanup_labels(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_labels_cleanup.json', neo4j_session, common_job_parameters)


def sync_labels(
    neo4j_session: neo4j.Session, data: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    if len(data) > 0:
        labels_list = get_labels_list(data)
        if len(labels_list) > 0:
            load_labels(neo4j_session, labels_list, update_tag)

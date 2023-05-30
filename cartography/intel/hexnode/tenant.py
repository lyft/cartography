import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hexnode.tenant import HexnodeTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: Session,
    api_url: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    data = [{'id': common_job_parameters['TENANT']}]
    load(neo4j_session, data, common_job_parameters)


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    tenant_query = build_ingestion_query(HexnodeTenantSchema())
    load_graph_data(
        neo4j_session,
        tenant_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )

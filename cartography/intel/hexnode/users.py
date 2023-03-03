import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hexnode.user import HexnodeUserSchema
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
    users = get(api_session, api_url)
    load(neo4j_session, users, common_job_parameters)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    users = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/users/', params=params, timeout=_TIMEOUT)
    req.raise_for_status()

    for r in req.json()['results']:
        users.append(r)

    if req.json().get('next') is not None:
        users += get(api_session, api_url, page=page + 1)

    return users


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    user_query = build_ingestion_query(HexnodeUserSchema())
    load_graph_data(
        neo4j_session,
        user_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
        tenant=common_job_parameters['TENANT'],
    )

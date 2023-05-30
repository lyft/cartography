import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hexnode.policy import HexnodePolicySchema
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
    policies = get(api_session, api_url)
    formatted_policies = transform(policies)
    load(neo4j_session, formatted_policies, common_job_parameters)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    policies = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/policy/', params=params, timeout=_TIMEOUT)
    req.raise_for_status()

    for p in req.json()['results']:
        policies.append(p)

    if req.json().get('next') is not None:
        policies += get(api_session, api_url, page=page + 1)

    return policies


@timeit
def transform(policies: List[Dict]) -> List[Dict]:
    result = []
    for policy in policies:
        n_policy = policy.copy()
        n_policy['created_time'] = int(dt_parse.parse(policy['created_time']).timestamp() * 1000)
        n_policy['modified_time'] = int(dt_parse.parse(policy['modified_time']).timestamp() * 1000)
        result.append(n_policy)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    policy_query = build_ingestion_query(HexnodePolicySchema())
    load_graph_data(
        neo4j_session,
        policy_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
        tenant=common_job_parameters['TENANT'],
    )

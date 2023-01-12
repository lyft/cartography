import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    api_session: Session,
    api_url: str,
) -> None:
    policies = get(api_session, api_url)
    formatted_policies = transform(policies)
    load(neo4j_session, formatted_policies, update_tag)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    policies = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/policy/', params=params, timeout=10)
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
        policy['created_time'] = dt_parse.parse(policy['created_time'])
        policy['modified_time'] = dt_parse.parse(policy['modified_time'])
        result.append(policy)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:

    query = """
    UNWIND $PolicyData as policy
    MERGE (p:HexnodePolicy{id: policy.id})
    ON CREATE set p.firstseen = timestamp()
    SET p.lastupdated = $UpdateTag,
    p.id = policy.id,
    p.name = policy.name,
    p.description = policy.description,
    p.version = policy.version,
    p.archived = policy.archived,
    p.ios_configured = policy.ios_configured,
    p.android_configured = policy.android_configured,
    p.windows_configured = policy.windows_configured,
    p.created_time = policy.created_time,
    p.modified_time = policy.modified_time
    """
    neo4j_session.run(
        query,
        PolicyData=data,
        UpdateTag=update_tag,
    )

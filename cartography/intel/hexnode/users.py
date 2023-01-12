import logging
from typing import Any, Dict, List, Tuple

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
    api_url: str
) -> None:
    users = get(api_session, api_url)
    load(neo4j_session, users, update_tag)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    users = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/users/', params=params, timeout=10)
    req.raise_for_status()

    for r in req.json()['results']:
        users.append(r)

    if req.json().get('next') is not None:
        users += get(api_session, api_url, page = page + 1)

    return users


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:

    query = """
    UNWIND $UserData as user
    MERGE (u:HexnodeUser{id: user.id})
    ON CREATE set u.firstseen = timestamp()
    SET u.lastupdated = $UpdateTag,
    u.id = user.id,
    u.name = user.name,
    u.email = user.email,
    u.phone = user.phoneno,
    u.domain = user.domain

    MERGE (h:Human {email: coalesce(user.email, "None")})
    ON CREATE set h.firstseen = timestamp()
    SET h.lastupdated = $UpdateTag

    MERGE (h)-[r:IDENTITY_HEXNODE]->(u)
    """

    neo4j_session.run(
        query,
        UserData=data,
        UpdateTag=update_tag,
    )

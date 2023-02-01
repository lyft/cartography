import logging
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.intel.lastpass.schema import LastpassUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    lastpass_cid: str,
    lastpass_provhash: str,
) -> None:
    users = get(lastpass_cid, lastpass_provhash)
    formated_users = transform(users)
    load(neo4j_session, formated_users, update_tag)


@timeit
def get(lastpass_cid: str, lastpass_provhash: str) -> dict:
    payload = {
        'cid': lastpass_cid,
        'provhash': lastpass_provhash,
        'cmd': 'getuserdata',
        'data': None,
    }
    session = Session()
    req = session.post('https://lastpass.com/enterpriseapi.php', data=payload, timeout=20)
    req.raise_for_status()
    return req.json()


@timeit
def transform(api_result: dict) -> List[Dict]:
    result: List[dict] = []
    for uid, user in api_result['Users'].items():
        n_user = user.copy()
        n_user['id'] = int(uid)
        for k in ('created', 'last_pw_change', 'last_login'):
            if n_user[k] == '':
                n_user.pop(k)
            n_user[k] = int(dt_parse.parse(user[k]).timestamp() * 1000)
        result.append(n_user)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:

    ingestion_query = build_ingestion_query(LastpassUserSchema())

    load_graph_data(
        neo4j_session,
        ingestion_query,
        data,
        lastupdated=update_tag,
    )

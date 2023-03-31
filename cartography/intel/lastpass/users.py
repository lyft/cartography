import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.lastpass.tenant import LastpassTenantSchema
from cartography.models.lastpass.user import LastpassUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    lastpass_provhash: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    users = get(lastpass_provhash, common_job_parameters)
    formated_users = transform(users)
    load(neo4j_session, formated_users, common_job_parameters)


@timeit
def get(lastpass_provhash: str, common_job_parameters: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        'cid': common_job_parameters['LASTPASS_CID'],
        'provhash': lastpass_provhash,
        'cmd': 'getuserdata',
        'data': None,
    }
    session = Session()
    req = session.post('https://lastpass.com/enterpriseapi.php', data=payload, timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def transform(api_result: dict) -> List[Dict]:
    result: List[dict] = []
    for uid, user in api_result['Users'].items():
        n_user = user.copy()
        n_user['id'] = int(uid)
        for k in ('created', 'last_pw_change', 'last_login'):
            n_user[k] = int(dt_parse.parse(user[k]).timestamp() * 1000) if user[k] else None
        result.append(n_user)
    return result


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    user_query = build_ingestion_query(LastpassUserSchema())
    tenant_query = build_ingestion_query(LastpassTenantSchema())

    load_graph_data(
        neo4j_session,
        tenant_query,
        [{'id': common_job_parameters['LASTPASS_CID']}],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )

    load_graph_data(
        neo4j_session,
        user_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
        tenant_id=common_job_parameters['LASTPASS_CID'],
    )

import logging
from typing import Dict, List

import neo4j
from requests import Session
from dateutil import parser as dt_parse

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    lastpass_cid: str,
    lastpass_provhash: str
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
        'data': None
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
        n_user['created'] = dt_parse.parse(user['created'])
        n_user['last_pw_change'] = dt_parse.parse(user['last_pw_change'])
        n_user['last_login'] = dt_parse.parse(user['last_login'])
        result.append(n_user)
    return result

def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:

    query = """
    UNWIND $UserData as user
    MERGE (u:LastpassUser{id: user.id})
    ON CREATE set u.firstseen = timestamp()
    SET u.lastupdated = $UpdateTag,
    u.id = user.id,
    u.name = user.fullname,
    u.email = user.username,
    u.created = user.created,
    u.last_pw_change = user.last_pw_change,
    u.last_login = user.last_login,
    u.neverloggedin = user.neverloggedin,
    u.disabled = user.disabled,
    u.admin = user.admin,
    u.totalscore = user.totalscore,
    u.mpstrength = user.mpstrength,
    u.sites = user.sites,
    u.notes = user.notes,
    u.formfills = user.formfills,
    u.applications = user.applications,
    u.attachments = user.attachments,
    u.password_reset_required = user.password_reset_required,
    u.multifactor = user.multifactor
    """

    neo4j_session.run(
        query,
        UserData=data,
        UpdateTag=update_tag,
    )

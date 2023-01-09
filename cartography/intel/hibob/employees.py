import logging
from typing import Any
from typing import Dict
from typing import List

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
) -> None:
    employees = get(api_session)
    transformed_employees = transform(employees)
    load(neo4j_session, transformed_employees, update_tag)


@timeit
def get(api_session: Session) -> Dict[str, Any]:
    req = api_session.get('https://api.hibob.com/v1/people', timeout=10)
    req.raise_for_status()
    return req.json()


@timeit
def transform(response_objects: Dict[str, List]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only
    :param response_objects:
    :return: list of dictionary objects as defined in /docs/schema/hibob.md
    """
    users: List[Dict] = []
    for user in response_objects['employees']:
        user['work']['startDate'] = dt_parse.parse(user['work']['startDate'])
        users.append(user)
    return users


def load(
    neo4j_session: neo4j.Session, data: List[Dict], update_tag: int,
) -> None:
    """
    Transform and load employees information
    """

    query = """
    UNWIND $UserData as user
    MERGE (ou:HiBobDepartment{id: user.work.department})
    ON CREATE SET ou.firstseen = timestamp()
    SET ou.name = user.work.department,
    ou.lastupdated = $UpdateTag

    MERGE (h:Human{email: user.email})
    ON CREATE SET h.firstseen = timestamp()
    SET h.lastupdated = $UpdateTag,
    h.name = user.displayName,
    h.family_name = user.surname,
    h.given_name = user.firstName,
    h.gender = user.home.localGender

    MERGE (u:HiBobEmployee{id: user.id})
    ON CREATE set u.firstseen = timestamp()
    SET u.user_id = user.id,
    u.name = user.displayName,
    u.family_name = user.surname,
    u.given_name = user.firstName,
    u.gender = user.home.localGender,
    u.email = user.email,
    u.private_mobile = user.home.mobilePhone,
    u.private_phone = user.home.privatePhone,
    u.private_email = user.home.privateEmail,
    u.start_date = user.work.startDate,
    u.is_manager = user.work.isManager,
    u.work_phone = user.work.workPhone,
    u.work_office = user.work.site,
    u.lastupdated = $UpdateTag

    MERGE (m:HiBobEmployee{id: coalesce(user.work.reportsTo.id, "None")})
    ON CREATE set m.firstseen = timestamp()
    SET m.email = user.work.reportsTo.email,
    m.lastupdated = $UpdateTag

    MERGE (h)-[rh:IS_EMPLOYEE]->(u)
    ON CREATE SET rh.firstseen = timestamp()
    SET rh.lastupdated = $UpdateTag

    MERGE (u)-[rm:MANAGED_BY]->(m)
    ON CREATE SET rm.firstseen = timestamp()
    SET rm.lastupdated = $UpdateTag

    MERGE (u)-[r:MEMBER_OF]->(ou)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        UserData=data,
        UpdateTag=update_tag,
    )

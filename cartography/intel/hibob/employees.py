import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session
from dateutil import parser as dt_parse

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_employees(
    neo4j_session: neo4j.Session,
    update_tag: int,
    api_session: Session,
) -> None:
    employees = get_employees(api_session)
    employees = transform_employees(employees)
    load_employees_data(neo4j_session, employees, update_tag)


@timeit
def get_employees(api_session: Session) -> List[Dict[str, Any]]:
    req = api_session.get('https://api.hibob.com/v1/people', timeout=10)
    req.raise_for_status()
    return req.json()

@timeit
def transform_employees(response_objects: Dict[str, List]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only
    :param response_objects:
    :return: list of dictionary objects as defined in /docs/schema/hibob.md
    """
    users: List[Dict] = []
    for user in response_objects['employees']:
        flattened_user = _dict_to_path(user)
        flattened_user['work.startDate'] = dt_parse.parse(flattened_user['work.startDate'])
        users.append(user)
    return users


def load_employees_data(
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
    h.name = user.fullName,
    h.family_name = user.surname,
    h.given_name = user.firstName,
    h.gender = user.home.localGender

    MERGE (u:HiBobEmployee{id: user.id})
    ON CREATE set u.firstseen = timestamp()
    SET u.user_id = user.is,
    u.name = user.fullName,
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

    MERGE (h)-[rh:EMPLOYEE]->(u)
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

def _dict_to_path(dict_: dict) -> dict:
    """ Transforms a multi level dict to a single level one:

    Method used to transform a dict to a flat dict.
    ex:
        {"foo": {"bar": "test"}
        becomes
        {"foo.bar": "test"}

    Args:
        dict_: dict to transform

    Returns:
        dict: a flat dict
    """
    result = {}
    for k, values in dict_.items():
        if isinstance(values, dict):
            for sub_k, sub_values in _dict_to_path(values).items():
                result[f"{k}.{sub_k}"] = sub_values
        else:
            result[k] = values
    return result

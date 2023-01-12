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
    groups = get(api_session, api_url)
    formated_groups, group_membership, group_policies = transform(groups)
    load(neo4j_session, formated_groups, group_membership, group_policies, update_tag)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    groups = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/devicegroups/', params=params, timeout=10)
    req.raise_for_status()

    for r in req.json()['results']:
        # Sub request for details
        sub_req = api_session.get(f"{api_url}/devicegroups/{r['id']}/", params=params, timeout=10)
        sub_req.raise_for_status()
        for k, v in sub_req.json().items():
            r[k] = v
        groups.append(r)

    if req.json().get('next') is not None:
        groups += get(api_session, api_url, page=page + 1)

    return groups


@timeit
def transform(groups: List[Dict]) -> Tuple[List[Dict], List[Dict[str, int]], List[Dict[str, int]]]:
    formated_groups = []
    group_membership = []
    group_policies = []
    for group in groups:
        group['modified_date'] = dt_parse.parse(group['modified_date'])
        for d in group['devices']:
            group_membership.append({'group': group['id'], 'device': d['id']})
        for p in group['policy']:
            group_policies.append({'group': group['id'], 'policy': p['id']})
        formated_groups.append(group)
    return formated_groups, group_membership, group_policies


def load(
    neo4j_session: neo4j.Session,
    groups: List[Dict],
    group_membership: List[Dict],
    group_policies: List[Dict],
    update_tag: int,
) -> None:

    query_groups = """
    UNWIND $GroupData as group
    MERGE (g:HexnodeDeviceGroup{id: group.id})
    ON CREATE set g.firstseen = timestamp()
    SET g.lastupdated = $UpdateTag,
    g.id = group.id,
    g.name = group.groupname,
    g.description = group.description,
    g.group_type = group.grouptype,
    g.modified_date = group.modified_date
    """

    query_membership = """
    UNWIND $MembershipData as ms
    MATCH (g:HexnodeDeviceGroup{id: ms.group}), (d:HexnodeDevice{id: ms.device})
    MERGE (d)-[r:MEMBER_OF]->(g)
    ON CREATE set r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    query_policy = """
    UNWIND $PolicyData as policy
    MATCH (g:HexnodeDeviceGroup{id: policy.group}), (p:HexnodePolicy{id: policy.policy})
    MERGE (g)-[r:APPLIES_POLICY]->(p)
    ON CREATE set r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    neo4j_session.run(query_groups, GroupData=groups, UpdateTag=update_tag)
    neo4j_session.run(query_membership, MembershipData=group_membership, UpdateTag=update_tag)
    neo4j_session.run(query_policy, PolicyData=group_policies, UpdateTag=update_tag)

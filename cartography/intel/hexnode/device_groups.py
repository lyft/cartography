import itertools
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dt_parse
from requests import Session

from cartography.client.core.tx import load_graph_data
from cartography.graph.querybuilder import build_ingestion_query
from cartography.models.hexnode.devicegroup import HexnodeDeviceGroupSchema
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
    groups = get(api_session, api_url)
    formated_groups = transform(groups)
    load(neo4j_session, formated_groups, common_job_parameters)


@timeit
def get(api_session: Session, api_url: str, page: int = 1) -> List[Dict]:
    groups = []
    params = {'per_page': 100}
    if page > 1:
        params['page'] = page

    req = api_session.get(f'{api_url}/devicegroups/', params=params, timeout=10)
    req.raise_for_status()

    for r in req.json()['results']:
        sub_req = api_session.get(f"{api_url}/devicegroups/{r['id']}/", params=params, timeout=10)
        sub_req.raise_for_status()
        for k, v in sub_req.json().items():
            r[k] = v
        groups.append(r)

    if req.json().get('next') is not None:
        groups += get(api_session, api_url, page=page + 1)

    return groups


@timeit
def transform(groups: List[Dict]) -> List[Dict]:
    formated_groups = []
    for group in groups:
        if len(group['devices']) == 0 and len(group['policy']) == 0:
            n_group = group.copy()
            n_group['modified_date'] = int(dt_parse.parse(group['modified_date']).timestamp() * 1000)
            formated_groups.append(n_group)
        else:
            # This will duplicate group to handle high cardinality (see https://github.com/lyft/cartography/issues/1131)
            for combination in itertools.zip_longest(group['devices'], group['policy']):
                n_group = group.copy()
                n_group['modified_date'] = int(dt_parse.parse(group['modified_date']).timestamp() * 1000)
                if combination[0] is not None:
                    n_group['device_id'] = combination[0]['id']
                if combination[1] is not None:
                    n_group['policy_id'] = combination[1]['id']
                formated_groups.append(n_group)
    return formated_groups


def load(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:

    policy_query = build_ingestion_query(HexnodeDeviceGroupSchema())
    load_graph_data(
        neo4j_session,
        policy_query,
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
        tenant=common_job_parameters['TENANT'],
    )

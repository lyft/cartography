import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.intel.gandi.utils import GandiAPI
from cartography.models.gandi.organization import GandiOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    gandi_session: GandiAPI,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    orgs = get(gandi_session)
    load_organizations(neo4j_session, orgs, update_tag)


@timeit
def get(gandi_session: GandiAPI) -> List[Dict[str, Any]]:
    return gandi_session.get_organizations()


def load_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GandiOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )

import logging

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def sync(neo4j_session, credentials, subscription_id, sync_tag, common_job_parameters):
    # TODO: start Azure Compute's sync
    print('inside azure Compute sync')

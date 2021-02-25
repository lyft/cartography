import logging

from digitalocean import Manager
from cartography.intel.digitalocean import compute, platform
from cartography.util import timeit


logger = logging.getLogger(__name__)

@timeit
def start_digitalocean_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    manager = Manager(token="")

    """
    Get Account ID related to this credentials and pass it along in `common_job_parameters` to avoid cleaning up other
    accounts resources 
    """
    account_id = platform.sync(neo4j_session, manager, config.update_tag, common_job_parameters)
    common_job_parameters["DO_ACCOUNT_ID"] = account_id

    compute.sync(neo4j_session, manager, config.update_tag, common_job_parameters)
    return

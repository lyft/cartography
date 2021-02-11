import logging

from digitalocean import Manager
from cartography.intel.digitalocean import droplets
from cartography.util import timeit


logger = logging.getLogger(__name__)

@timeit
def start_digitalocean_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    manager = Manager(token="")
    droplets.sync(neo4j_session, manager, config.update_tag, common_job_parameters)
    return

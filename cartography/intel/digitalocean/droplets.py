import logging

from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def sync(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    logger.info("Syncing Droplets")
    get_droplets(manager)

def get_droplets(manager):
    my_droplets = manager.get_all_droplets()
    print(my_droplets)



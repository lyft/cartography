import logging

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

@timeit
def sync(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    sync_droplets(neo4j_session, manager, digitalocean_update_tag, common_job_parameters)

@timeit
def sync_droplets(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    logger.info("Syncing Droplets")
    account_id = common_job_parameters['DO_ACCOUNT_ID']
    droplets_res = get_droplets(manager)
    droplets = transform_droplets(droplets_res, account_id)
    load_droplets(neo4j_session, droplets, digitalocean_update_tag)
    cleanup_droplets(neo4j_session, common_job_parameters)

@timeit
def get_droplets(manager):
    return manager.get_all_droplets()

@timeit
def transform_droplets(droplets_res: list, account_id):
    droplets = list()
    for d in droplets_res:
        droplet = {}
        droplet['id'] = d.id
        droplet['name'] = d.name
        droplet['locked'] = d.locked
        droplet['status'] = d.status
        droplet['features'] = d.features
        droplet['region'] = d.region['slug']
        droplet['created_at'] = d.created_at
        droplet['image'] = d.image['slug']
        droplet['size'] = d.size['slug']
        droplet['kernel'] = d.kernel
        droplet['tags'] = d.tags
        droplet['volumes'] = d.volume_ids
        droplet['vpc_uuid'] = d.vpc_uuid
        droplet['ip_address'] = d.ip_address
        droplet['private_ip_address'] = d.private_ip_address
        droplet['ip_v6_address'] = d.ip_v6_address
        droplet['account_id'] = account_id
        droplets.append(droplet)
    return droplets

@timeit
def load_droplets(neo4j_session, data, digitalocean_update_tag):
    query = """
        MERGE (a:DOAccount{id:{AccountId}})
        ON CREATE SET a.firstseen = timestamp()
        SET a.lastupdated = {digitalocean_update_tag}
        
        MERGE (d:DODroplet{id:{DropletId}})
        ON CREATE SET d.firstseen = timestamp()
        SET d.account_id = {AccountId}, 
        d.name = {Name},
        d.locker = {Locked},
        d.status = {Status},
        d.features = {Features},
        d.region = {RegionSlug},
        d.created_at = {CreatedAt},
        d.image = {ImageSlug},
        d.size = {SizeSlug},
        d.kernel = {Kernel},
        d.ip_address = {IpAddress},
        d.private_ip_address = {PrivateIpAddress},
        d.ip_v6_address = {IpV6Address},
        d.tags = {Tags},
        d.volumes = {Volumes},
        d.vpc_uuid = {VpcUuid},
        d.lastupdated = {digitalocean_update_tag}
        WITH d, a

        MERGE (a)-[r:RESOURCE]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = {digitalocean_update_tag}
        """
    for droplet in data:
        neo4j_session.run(
            query,
            AccountId = droplet['account_id'],
            DropletId = droplet['id'],
            Name = droplet['name'],
            Locked = droplet['locked'],
            Status = droplet['status'],
            Features = droplet['features'],
            RegionSlug = droplet['region'],
            CreatedAt = droplet['created_at'],
            ImageSlug = droplet['image'],
            SizeSlug = droplet['size'],
            IpAddress = droplet['ip_address'],
            PrivateIpAddress = droplet['private_ip_address'],
            IpV6Address = droplet['ip_v6_address'],
            Kernel = droplet['kernel'],
            Tags = droplet['tags'],
            Volumes = droplet['volumes'],
            VpcUuid = droplet['vpc_uuid'],
            digitalocean_update_tag=digitalocean_update_tag,
        )
    return

@timeit
def cleanup_droplets(neo4j_session, common_job_parameters):
    """
        Delete out-of-date DigitalOcean droplets and relationships
        :param neo4j_session: The Neo4j session
        :param common_job_parameters: dict of other job parameters to pass to Neo4j
        :return: Nothing
        """
    run_cleanup_job('digitalocean_droplet_cleanup.json', neo4j_session, common_job_parameters)
    return
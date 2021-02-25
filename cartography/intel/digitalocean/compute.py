import logging

from cartography.util import run_cleanup_job
from cartography.util import timeit
from digitalocean import Droplet

logger = logging.getLogger(__name__)

@timeit
def sync(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    sync_droplets(neo4j_session, manager, digitalocean_update_tag, common_job_parameters)

@timeit
def sync_droplets(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    logger.info("Syncing Droplets")
    droplets_res = get_droplets(manager)
    droplets = transform_droplets(droplets_res)
    load_droplets(neo4j_session, droplets, digitalocean_update_tag)
    cleanup_droplets(neo4j_session, common_job_parameters)

def get_droplets(manager):
    return manager.get_all_droplets()

def transform_droplets(droplets_res: list):
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
        droplet['public_ips'] = _extract_droplet_ips_by_type_and_version(d.networks, 'public', 'v4')
        droplet['private_ips'] = _extract_droplet_ips_by_type_and_version(d.networks, 'private', 'v4')
        droplets.append(droplet)
    return droplets

def load_droplets(neo4j_session, data, digitalocean_update_tag):
    query = """
        MERGE (d:DODroplet{id:{DropletId}})
        ON CREATE SET d.firstseen = timestamp()
        SET d.name = {Name},
        d.locker = {Locked},
        d.status = {Status},
        d.features = {Features},
        d.region = {RegionSlug},
        d.created_at = {CreatedAt},
        d.image = {ImageSlug},
        d.size = {SizeSlug},
        d.kernel = {Kernel},
        d.private_ips = {PrivateIps},
        d.public_ips = {PublicIps},
        d.tags = {Tags},
        d.volumes = {Volumes},
        d.vpc_uuid = {VpcUuid},
        d.lastupdated = {digitalocean_update_tag}
        """
    for droplet in data:
        neo4j_session.run(
            query,
            DropletId = droplet['id'],
            Name = droplet['name'],
            Locked = droplet['locked'],
            Status = droplet['status'],
            Features = droplet['features'],
            RegionSlug = droplet['region'],
            CreatedAt = droplet['created_at'],
            ImageSlug = droplet['image'],
            SizeSlug = droplet['size'],
            PrivateIps = droplet['private_ips'],
            PublicIps = droplet['public_ips'],
            Kernel = droplet['kernel'],
            Tags = droplet['tags'],
            Volumes = droplet['volumes'],
            VpcUuid = droplet['vpc_uuid'],
            digitalocean_update_tag=digitalocean_update_tag,
        )
    return

def cleanup_droplets(neo4j_session, common_job_parameters):
    """
        Delete out-of-date DigitalOcean droplets and relationships
        :param neo4j_session: The Neo4j session
        :param common_job_parameters: dict of other job parameters to pass to Neo4j
        :return: Nothing
        """
    run_cleanup_job('digitalocean_droplet_cleanup.json', neo4j_session, common_job_parameters)
    return

def _extract_droplet_ips_by_type_and_version(networks, type_of_ip, version):
    result = list()
    v4_networks = networks[version]
    for n in v4_networks:
       if n['type'] == type_of_ip:
           result.append(n['ip_address'])

    return result
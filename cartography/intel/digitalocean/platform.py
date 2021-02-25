import logging

from cartography.util import run_cleanup_job
from cartography.util import timeit
from digitalocean import Account


logger = logging.getLogger(__name__)

@timeit
def sync(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    # Will return the Account ID related to this credentials, to be used for the rest of the resources
    account_id = sync_account(neo4j_session, manager, digitalocean_update_tag, common_job_parameters)
    return account_id

@timeit
def sync_account(neo4j_session, manager, digitalocean_update_tag, common_job_parameters):
    logger.info("Syncing Account")
    account_res = get_account(manager)
    account = transform_account(account_res)
    load_account(neo4j_session, account, digitalocean_update_tag)

    common_job_parameters['DO_ACCOUNT_ID'] = account['id']
    cleanup_account(neo4j_session, common_job_parameters)

    return account['id']

@timeit
def get_account(manager) -> Account:
    return manager.get_account()

@timeit
def transform_account(account_res):
    account = {
        'id': account_res.uuid,
        'uuid': account_res.uuid,
        'droplet_limit': account_res.droplet_limit,
        'floating_ip_limit': account_res.floating_ip_limit,
        'status': account_res.status
    }
    return account

@timeit
def load_account(neo4j_session, account, digitalocean_update_tag):
    query = """
            MERGE (a:DOAccount{id:{AccountId}})
            ON CREATE SET a.firstseen = timestamp()
            SET a.uuid = {Uuid},
            a.droplet_limit = {DropletLimit},
            a.floating_ip_limit = {FloatingIpLimit},
            a.status = {Status},
            a.lastupdated = {digitalocean_update_tag}
            """
    neo4j_session.run(
        query,
        AccountId = account['id'],
        Uuid = account['uuid'],
        DropletLimit = account['droplet_limit'],
        FloatingIpLimit = account['floating_ip_limit'],
        Status = account['status'],
        digitalocean_update_tag=digitalocean_update_tag,
    )
    return

@timeit
def cleanup_account(neo4j_session, common_job_parameters):
    """
            Delete out-of-date DigitalOcean accounts and relationships
            :param neo4j_session: The Neo4j session
            :param common_job_parameters: dict of other job parameters to pass to Neo4j
            :return: Nothing
            """
    run_cleanup_job('digitalocean_account_cleanup.json', neo4j_session, common_job_parameters)
    return
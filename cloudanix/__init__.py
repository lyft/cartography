from cartography.util import run_cleanup_job
from cartography.util import timeit


@timeit
def run(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "workspace_name": config.params['workspace']['name'],
        "workspace_account_id": config.params['workspace']['account_id'],
    }

    load_cloudanix_workspace(neo4j_session, config.update_tag, common_job_parameters)

    run_cleanup_job('cloudanix_workspace_cleanup.json', neo4j_session, common_job_parameters)


def load_cloudanix_workspace(neo4j_session, update_tag, common_job_parameters):
    query = """
    MERGE (w:CloudanixWorkspace{id: {WORKSPACE_ID}})
    ON CREATE SET w.firstseen = timestamp(), w.lastupdated = {UPDATE_TAG}, 
    w.name = {WORKSPACE_NAME}, w.account_id= {WORKSPACE_ACCOUNT_ID}
    SET w.lastupdated = {UPDATE_TAG}, w.name = {WORKSPACE_NAME}, w.account_id= {WORKSPACE_ACCOUNT_ID}
    """

    neo4j_session.run(
        query,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        WORKSPACE_NAME=common_job_parameters['workspace_name'],
        WORKSPACE_ACCOUNT_ID=common_job_parameters['workspace_account_id'],
        UPDATE_TAG=update_tag,
    )

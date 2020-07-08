from cartography.intel.jamf import computers
from cartography.util import timeit


@timeit
def start_jamf_ingestion(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    computers.sync(neo4j_session, config.jamf_base_uri, config.jamf_user, config.jamf_password, common_job_parameters)

import logging

from cartography.intel.jamf.util import call_jamf_api
from cartography.util import run_cleanup_job
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get_computer_groups(jamf_base_uri, jamf_user, jamf_password):
    return call_jamf_api("/computergroups", jamf_base_uri, jamf_user, jamf_password)


@timeit
def load_computer_groups(data, neo4j_session, update_tag):
    ingest_groups = """
    UNWIND {JsonData} as group
    MERGE (g:JamfComputerGroup{id: group.id})
    ON CREATE SET g.name = group.name,
    g.firstseen = timestamp()
    SET g.is_smart = group.is_smart,
    g.lastupdated = {UpdateTag}
    """
    groups = data.get("computer_groups")
    neo4j_session.run(ingest_groups, JsonData=groups, UpdateTag=update_tag)


@timeit
def cleanup(neo4j_session, common_job_parameters):
    run_cleanup_job('jamf_import_computers_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_computer_groups(neo4j_session, update_tag, jamf_base_uri, jamf_user, jamf_password):
    groups = get_computer_groups(jamf_base_uri, jamf_user, jamf_password)
    load_computer_groups(groups, neo4j_session, update_tag)


@timeit
def sync(neo4j_session, jamf_base_uri, jamf_user, jamf_password, common_job_parameters):
    sync_computer_groups(neo4j_session, common_job_parameters['UPDATE_TAG'], jamf_base_uri, jamf_user, jamf_password)

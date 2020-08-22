from importlib.resources import read_text

from cartography.graph.job import GraphJob


def run_analysis_job(filename, neo4j_session, common_job_parameters):
    GraphJob.run_from_json(
        neo4j_session,
        read_text(
            'cartography.data.jobs.analysis',
            filename,
        ),
        common_job_parameters,
    )


def run_cleanup_job(filename, neo4j_session, common_job_parameters):
    GraphJob.run_from_json(
        neo4j_session,
        read_text(
            'cartography.data.jobs.cleanup',
            filename,
        ),
        common_job_parameters,
    )

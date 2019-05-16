import cartography.util
import sys
if sys.version_info >= (3, 7):
    from importlib.resources import contents
else:
    from importlib_resources import contents


def test_analysis_jobs_actually_execute(neo4j_session):
    for job_name in contents('cartography.data.jobs.analysis'):
        cartography.util.run_analysis_job(job_name, neo4j_session, {})


def test_cleanup_jobs_actually_execute(neo4j_session):
    for job_name in contents('cartography.data.jobs.cleanup'):
        cartography.util.run_cleanup_job(job_name, neo4j_session, {})

import json
import sys
if sys.version_info >= (3, 7):
    from importlib.resources import contents, read_text
else:
    from importlib_resources import contents, read_text


def test_analysis_jobs_actually_execute(neo4j_session):
    for job_name in contents('cartography.data.jobs.analysis'):
        if not job_name.endswith('.json'):
            continue
        blob = read_text('cartography.data.jobs.analysis', job_name)
        json.loads(blob)


def test_cleanup_jobs_actually_execute(neo4j_session):
    for job_name in contents('cartography.data.jobs.cleanup'):
        if not job_name.endswith('json'):
            continue
        blob = read_text('cartography.data.jobs.cleanup', job_name)
        json.loads(blob)

import json
import pytest
import sys
if sys.version_info >= (3, 7):
    from importlib.resources import contents, read_text
else:
    from importlib_resources import contents, read_text


def test_analysis_jobs_actually_execute():
    for job_name in contents('cartography.data.jobs.analysis'):
        if not job_name.endswith('.json'):
            continue
        blob = read_text('cartography.data.jobs.analysis', job_name)
        try:
            json.loads(blob)
        except Exception as e:
            pytest.fail("json.loads failed for analysis job '{}' with exception: {}".format(job_name, e))


def test_cleanup_jobs_actually_execute():
    for job_name in contents('cartography.data.jobs.cleanup'):
        if not job_name.endswith('json'):
            continue
        blob = read_text('cartography.data.jobs.cleanup', job_name)
        try:
            json.loads(blob)
        except Exception as e:
            pytest.fail("json.loads failed for cleanup job '{}' with exception: {}".format(job_name, e))

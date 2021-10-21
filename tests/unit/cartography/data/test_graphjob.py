from cartography.graph.job import GraphJob
from tests.data.jobs.sample import SAMPLE_CLEANUP_JOB


def test_graphjob_from_json():
    # Act
    job: GraphJob = GraphJob.from_json(SAMPLE_CLEANUP_JOB)

    # Assert that the job was created from json string contents correctly
    assert job.name == "cleanup stale resources"
    assert len(job.statements) == 3
    assert job.short_name is None

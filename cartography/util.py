import logging
import sys

import botocore

from cartography.graph.job import GraphJob

if sys.version_info >= (3, 7):
    from importlib.resources import open_binary, read_text
else:
    from importlib_resources import open_binary, read_text

logger = logging.getLogger(__name__)


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


def load_resource_binary(package, resource_name):
    return open_binary(package, resource_name)


# The statsd client used for observability.  This is `None` unless cartography.config.statsd_enabled is True.
stats_client = None


def timeit(method):
    """
    This decorator uses statsd to time the execution of the wrapped method and sends it to the statsd server.
    This is only active if config.statsd_enabled is True.
    :param method: The function to measure execution
    """
    def timed(*args, **kwargs):
        if stats_client:
            # Example metric name "cartography.intel.aws.iam.get_group_membership_data"
            metric_name = f"{method.__module__}.{method.__name__}"
            timer = stats_client.timer(metric_name)
            timer.start()
            result = method(*args, **kwargs)
            timer.stop()
            return result
        else:
            # statsd is disabled, so don't time anything
            return method(*args, **kwargs)

    return timed


def aws_handle_regions(func):
    ERROR_CODES = [
        'AccessDeniedException',
        'UnrecognizedClientException',
        'InvalidClientTokenId',
        'AuthFailure',
    ]

    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            # The account is not authorized to use this service in this region
            # so we can continue without raising an exception
            if e.response['Error']['Code'] in ERROR_CODES:
                logger.warning("{} in this region. Skipping...".format(e.response['Error']['Message']))
                return []
            else:
                raise
    return inner_function

from cartography.util import stats_client


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

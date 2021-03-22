from statsd import StatsClient
from statsd.client.timer import Timer


class ScopedStatsClient:
    """
    A Proxy object for an underlying statsd client.
    Adds a new call, get_scoped_stats_client(scope), which returns a new proxy to the same
    client which will prefix all calls to underlying methods with the scoped prefix:
    new_client = client.get_scoped_stats_client('a')
    new_client.incr('b') # Metric name = a.b
    This can be nested:
    newer_client = new_client.get_scoped_stats_client('subsystem')
    newer_client.incr('bad') # Metric name = a.subsystem.bad
    """

    def __init__(self, client: StatsClient, prefix: str = None):
        self._client = client
        self._scope_prefix = prefix

    def get_scoped_stats_client(self, scope: str):
        """
        This method returns a new proxy to the same client
        which will prefix all calls to underlying methods with the scoped prefix
        """
        if not self._scope_prefix:
            prefix = scope
        else:
            prefix = self._scope_prefix + "." + scope
        return ScopedStatsClient(self._client, prefix)

    def is_enabled(self) -> bool:
        return self._client is not None

    def incr(self, stat: str, count: int = 1, rate: float = 1.0) -> None:
        """
        This method uses statsd to increment a counter.
        :param stat: the name of the counter metric stat (string) to increment
        :param count: the amount (integer) to increment by. May be negative
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            self._client.incr(self._scope_prefix + "." + stat, count, rate)

    def timer(self, stat: str, rate: float = 1.0) -> Timer:
        """
        This method uses statsd to retrieve a timer.
        When Timer.stop() is called, a timing stat will automatically be sent to statsd
        :param stat: the name of the timer metric stat (string) to report
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            return self._client.timer(stat, rate)
        return None
